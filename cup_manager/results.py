import logging
from datetime import datetime
from peewee import *

from pyplanet.apps.core.maniaplanet import callbacks as mp_signals
from pyplanet.apps.core.trackmania import callbacks as tm_signals
from pyplanet.apps.core.shootmania import callbacks as sm_signals
from pyplanet.contrib.setting import Setting
from pyplanet.contrib.command import Command

from .models import PlayerScore, TeamScore, MatchInfo, CupInfo
from .views import MatchHistoryView, TextResultsView, MatchesView, ResultsView
from .app_types import GenericPlayerScore, GenericTeamScore, TeamPlayerScore, ScoreSortingPresets

logger = logging.getLogger(__name__)

class ResultsCupManager:
	def __init__(self, app) -> None:
		self.app = app
		self.instance = app.instance
		self.context = app.context

		self._match_start_time = 0
		self._match_map_name = ''
		self._match_mx_id = ''
		self._match_players_scored = []
		self._match_teams_scored = []
		self._match_info_created = False
		self._setting_match_history_amount = None
		self._view_cache_matches = []
		self._view_cache_scores = {}
		self._view_cache_team_scores = {}
		self._match_start_notify_list = []
		self._scores_update_notify_list = []

		self._setting_match_history_amount = Setting(
			'match_history_amount', 'Amount of Saved Matches', Setting.CAT_BEHAVIOUR, type=int,
			description='Set this number to the number of previous matches you want to save in the database.',
			default=100
		)

		MatchesView.set_get_data_method(self.get_data_matches)


	async def on_start(self) -> None:
		self.context.signals.listen(tm_signals.scores, self._tm_signals_scores)
		self.context.signals.listen(mp_signals.map.map_start, self._mp_signals_map_map_start)
		self.context.signals.listen(mp_signals.map.map_end, self._mp_signals_map_map_end)
		self.context.signals.listen(sm_signals.base.scores, self._tm_signals_scores)

		await self.context.setting.register(self._setting_match_history_amount)

		await self.instance.permission_manager.register('results_cup', 'Handle match results from cup_manager', app=self.app, min_level=2, namespace=self.app.namespace)

		await self.instance.command_manager.register(
			Command(command='matches', aliases=['m'], namespace=self.app.namespace, target=self._command_matches,
				description='Display saved match history.'),
			Command(command='matches', aliases=['m'], namespace=self.app.namespace, target=self._command_matches,
				admin=True, perms='cup:results_cup', description='Display saved match history.'),
		)

		MatchHistoryView.add_button(self._button_export, 'Export', True, 25)
		ResultsView.add_button('Export', self._button_export, True)

		await self._handle_map_update('OnStart')

		scores = None
		try:
			if self.instance.game.game == 'sm':
				scores = await self.instance.gbx('Shootmania.GetScores')
			else:
				scores = await self.instance.gbx('Trackmania.GetScores')
		except:
			pass

		if scores:
			await self._handle_player_score_update(scores['players'])


	async def _tm_signals_scores(self, players, teams, winner_team, use_teams, winner_player, section, **kwargs):
		if section == 'PreEndRound':
			# PreEndRound score callback shows round_points before they are added to match_points. For simplicity I only care about match_points.
			return
		if use_teams:
			await self._handle_team_score_update(teams)
		await self._handle_player_score_update(players)

		if self._scores_update_notify_list:
			for score_notify in self._scores_update_notify_list:
				await score_notify(match_start_time=self._match_start_time)
		logger.info("Update TM scores complete in _tm_signals_scores")


	async def _mp_signals_map_map_start(self, time, count, restarted, map, **kwargs):
		await self._handle_map_update('MapStart')


	async def _mp_signals_map_map_end(self, map, **kwargs):
		await self._handle_map_update('MapEnd')


	async def _handle_team_score_update(self, team_scores: list):
		new_scores = []
		for team_score in team_scores:
			try:
				new_score_id = team_score['id']
				new_score_name = team_score['name']
				new_score_score = team_score['map_points']
				new_scores.append(GenericTeamScore(new_score_id, new_score_name, new_score_score))

			except Exception as e:
				logger.error(f"Exception while recording scores for following team_score object: {str(team_score)}")
				logger.error(str(e))

		if new_scores:
			for new_score in new_scores:
				logger.info(new_score)
				if self._match_start_time != 0:
					await self._create_match_info()

					if new_score.id in self._match_teams_scored:
						await TeamScore.execute(
							TeamScore.update(
								name=new_score.name,
								score=new_score.score,
							).where(
								(TeamScore.team_id == new_score.id) & (TeamScore.map_start_time == self._match_start_time)
							)
						)
					else:
						self._match_teams_scored.append(new_score.id)
						await TeamScore.execute(
							TeamScore.insert(
								map_start_time=self._match_start_time,
								team_id=new_score.id,
								name=new_score.name,
								score=new_score.score,
							)
						)
					await self._invalidate_view_cache_team_scores(self._match_start_time)


	async def _handle_player_score_update(self, player_scores: list):
		current_script_lower = (await self.instance.mode_manager.get_current_script()).lower()
		new_scores = []
		for player_score in player_scores:
			try:
				new_score_login = player_score['login'] if 'login' in player_score else player_score['player'].login
				new_score_nick = player_score['name'] if 'name' in player_score else player_score['player'].nickname

				new_score_country = 'World'
				try:
					if 'player' in player_score and player_score['player'].flow.zone.country != None:
						new_score_country = player_score['player'].flow.zone.country
					else:
						logger.warning("player.flow.zone.country was None for login \"" + new_score_login + "\" nickname \"" + new_score_nick + "\". Defaulting to " + str(new_score_country))
				except Exception as e:
					logger.error("Exception while accessing country for login \"" + new_score_login + "\", nickname \"" + new_score_nick + "\": " + str(e))

				new_score_team = -1
				try:
					if 'player' in player_score and player_score['player'].flow.team_id != None:
						new_score_team = player_score['player'].flow.team_id
					else:
						logger.warning("player.flow.team_id was None for login \"" + new_score_login + "\" nickname \"" + new_score_nick + "\". Defaulting to " + str(new_score_team))
				except Exception as e:
					logger.error("Exception while accessing team_id for login \"" + new_score_login + "\", nickname \"" + new_score_nick + "\": " + str(e))

				if 'timeattack' in current_script_lower:
					new_score_score = player_score['best_race_time'] if 'best_race_time' in player_score else player_score['bestracetime']
					if new_score_score != -1:
						new_scores.append(GenericPlayerScore(new_score_login, new_score_nick, new_score_country, new_score_score, score2=0, team=new_score_team))

				elif 'laps' in current_script_lower:
					new_score_score = player_score['best_race_time'] if 'best_race_time' in player_score else player_score['bestracetime']
					new_score_score2 = len(player_score['best_race_checkpoints']) if 'best_race_checkpoints' in player_score else len(player_score['bestracecheckpoints'])
					if new_score_score != -1:
						new_scores.append(GenericPlayerScore(new_score_login, new_score_nick, new_score_country, new_score_score, score2=new_score_score2, team=new_score_team))

				else:
					new_score_score = player_score['map_points'] if 'map_points' in player_score else player_score['mappoints']
					if new_score_score != -1:
						new_scores.append(GenericPlayerScore(new_score_login, new_score_nick, new_score_country, new_score_score, score2=0, team=new_score_team))

			except Exception as e:
				logger.error(f"Exception while recording scores for following player_score object: {str(player_score)}")
				logger.error(str(e))

		if new_scores:
			for new_score in new_scores:
				logger.info(new_score)
				if self._match_start_time != 0:
					await self._create_match_info()

					try:
						if new_score.login in self._match_players_scored:
							logger.debug("Entry exists, updating score")
							await PlayerScore.execute(
								PlayerScore.update(
									nickname=new_score.nickname,
									country=new_score.country,
									score=new_score.score,
									score2=new_score.score2,
									team=new_score.team,
								).where(
									(PlayerScore.login == new_score.login) & (PlayerScore.map_start_time == self._match_start_time)
								)
							)
						else:
							logger.debug("No entry exists, creating score")
							self._match_players_scored.append(new_score.login)
							await PlayerScore.execute(
								PlayerScore.insert(
									map_start_time=self._match_start_time,
									login=new_score.login,
									nickname=new_score.nickname,
									country=new_score.country,
									score=new_score.score,
									score2=new_score.score2,
									team=new_score.team,
								)
							)
					except Exception as e:
						logger.error("Exception writing PlayerScore to database."
							+ f" map_start_time: {str(self._match_start_time)}, login: {str(new_score.login)},"
							+ f" nickname: {str(new_score.nickname)}, country: {str(new_score.country)}, score: {str(new_score.score)},"
							+ f" score2: {str(new_score.score2)}, team: {str(new_score.team)}")
					await self._invalidate_view_cache_scores(self._match_start_time)


	async def _create_match_info(self) -> None:
		if not self._match_info_created:
			logger.debug("Current match data does not exist, creating")
			self._match_info_created = True

			current_mode_script = await self.instance.mode_manager.get_current_script()
			current_map_uid = self.instance.map_manager.current_map.uid
			current_mx_id = ''
			if 'mx' in self.app.instance.apps.apps:
				try:
					mx_info = await self.app.instance.apps.apps['mx'].api.map_info(current_map_uid)
					if mx_info and len(mx_info) >= 1:
						current_mx_id = str(mx_info[0][0])
				except Exception as e:
					logger.error(f'Could not retrieve the map info from (T)MX API for the current map: {str(e)}')

			try:
				await MatchInfo.execute(MatchInfo.insert(
					map_start_time=self._match_start_time,
					mode_script=current_mode_script,
					map_name=self._match_map_name,
					map_uid=current_map_uid,
					mx_id=current_mx_id,
				))
			except Exception as e:
				logger.error("Exception while attempting to write map information to database."
					+ f" map_start_time: {str(self._match_start_time)}, mode_script: {str(current_mode_script)},"
					+ f" map_name: {str(self._match_map_name)}, map_uid: {str(current_map_uid)}, mx_id: {str(current_mx_id)}")
			await self._invalidate_view_cache_matches()


	async def _handle_map_update(self, section: str):
		if section == 'OnStart' or section == 'MapStart':
			self._match_start_time = int(datetime.now().timestamp())
			self._match_map_name = self.instance.map_manager.current_map.name
			self._match_players_scored = []
			self._match_teams_scored = []
			self._match_info_created = False
			if self._match_start_notify_list:
				for notify_method in self._match_start_notify_list:
					await notify_method(match_start_time=self._match_start_time)

		elif section == 'MapEnd':
			ended_map_start_time = self._match_start_time
			ended_map_map_name = self._match_map_name
			self._match_start_time = 0
			self._match_map_name = None
			self._match_players_scored = []
			self._match_teams_scored = []
			self._match_info_created = False

			await self._prune_match_history()
			match_data = await self.get_data_matches()
			for match in match_data:
				if match.map_start_time == ended_map_start_time:
					score_data = await self.get_data_scores(match.map_start_time, ScoreSortingPresets.get_preset(match.mode_script))
					await self.instance.chat(f'$ff0Saved $<$fff{str(len(score_data))}$> record(s) from map $<$fff{ended_map_map_name}$>')
					break
			else:
				await self.instance.chat(f'$ff0No records saved from map $<$fff{ended_map_map_name}$>')

		else:
			logger.error('Unexpected section reached in _handle_map_update: \"' + section + '\"')


	async def _prune_match_history(self):
		# TODO: Logic to not prune matches that are part of a cup
		match_data = await self.get_data_matches()
		map_times = [time.map_start_time for time in match_data]
		map_times.sort()
		match_limit = await self._setting_match_history_amount.get_value()

		while len(map_times) > match_limit:
			oldest_time = map_times[0]
			await PlayerScore.execute(PlayerScore.delete().where(PlayerScore.map_start_time == oldest_time))
			await MatchInfo.execute(MatchInfo.delete().where(MatchInfo.map_start_time == oldest_time))
			await TeamScore.execute(TeamScore.delete().where(TeamScore.map_start_time == oldest_time))
			await self._invalidate_view_cache_scores(oldest_time)
			await self._invalidate_view_cache_matches()
			await self._invalidate_view_cache_team_scores(oldest_time)
			map_times.pop(0)


	async def _command_matches(self, player, data, **kwargs):
		if await self.get_data_matches():
			view = MatchHistoryView(self.app, player)
			await view.display(player=player.login)
		else:
			await self.instance.chat('$f00No matches found', player)


	async def _invalidate_view_cache_matches(self):
		self._view_cache_matches = []


	async def _invalidate_view_cache_scores(self, map_start_time: int=0):
		if map_start_time == 0:
			self._view_cache_scores = {}
		elif map_start_time in self._view_cache_scores:
			del self._view_cache_scores[map_start_time]


	async def _invalidate_view_cache_team_scores(self, map_start_time: int=0):
		if map_start_time == 0:
			self._view_cache_team_scores = {}
		elif map_start_time in self._view_cache_team_scores:
			del self._view_cache_team_scores[map_start_time]


	async def _button_export(self, player, values, view: any, **kwargs):
		if view.scores_query:
			scores_data = await self.get_data_scores(view.scores_query, view.scores_sorting)

			match_info = []
			all_match_data = await self.get_data_matches()
			for match_data_info in all_match_data:
				if (isinstance(view.scores_query, int) and match_data_info.map_start_time == view.scores_query) or (isinstance(view.scores_query, list) and match_data_info.map_start_time in view.scores_query):
					match_info.append(match_data_info)

			text_view = TextResultsView(
				self,
				player,
				scores_data,
				match_info,
				TeamPlayerScore.score2_relevant(view.scores_sorting),
				TeamPlayerScore.score_team_relevant(view.scores_sorting)
			)

			if hasattr(view, 'cup_start_time'):
				cup_info = await self.app.active.get_data_specific_cup_info(view.cup_start_time)	# type: CupInfo
				text_view.cup_name = cup_info.cup_name
				text_view.cup_edition = 'Edition #' + str(cup_info.cup_edition)

			await text_view.display(player=player)


	async def register_match_start_notify(self, notify_method) -> None:
		if notify_method not in self._match_start_notify_list:
			self._match_start_notify_list.append(notify_method)


	async def register_scores_update_notify(self, notify_method) -> None:
		if notify_method not in self._scores_update_notify_list:
			self._scores_update_notify_list.append(notify_method)


	async def get_current_match_start_time(self) -> int:
		return self._match_start_time


	async def get_data_matches(self) -> 'list[MatchInfo]':
		if not self._view_cache_matches:
			map_history_query = await MatchInfo.execute(MatchInfo.select().order_by(MatchInfo.map_start_time.desc()))
			if len(map_history_query) > 0:
				self._view_cache_matches = list(map_history_query)	# type: list[MatchInfo]
		return self._view_cache_matches


	async def get_data_specific_matches(self, matches: any) -> 'list[MatchInfo]':
		lookup_matches = []
		if isinstance(matches, int):
			lookup_matches.append(matches)
		elif isinstance(matches, list):
			lookup_matches = matches
		else:
			logger.error(f"Unexpected type in get_data_specific_matches: {str(matches)}")

		all_matches = await self.get_data_matches()
		return [match for match in all_matches if match.map_start_time in lookup_matches]


	async def get_data_player_scores(self, map_start_time: int) -> 'list[PlayerScore]':
		if not (map_start_time in self._view_cache_scores and self._view_cache_scores[map_start_time]):
			scores_query = await PlayerScore.execute(PlayerScore.select().where(PlayerScore.map_start_time.in_([map_start_time])))
			if len(scores_query) > 0:
				self._view_cache_scores[map_start_time] = list(scores_query)
			else:
				self._view_cache_scores[map_start_time] = []
		return self._view_cache_scores[map_start_time]


	async def get_data_team_scores(self, map_start_time: int) -> 'list[TeamScore]':
		if not (map_start_time in self._view_cache_team_scores and self._view_cache_team_scores[map_start_time]):
			scores_query = await TeamScore.execute(TeamScore.select().where(TeamScore.map_start_time.in_([map_start_time])))
			if len(scores_query) > 0:
				self._view_cache_team_scores[map_start_time] = list(scores_query)
			else:
				self._view_cache_team_scores[map_start_time] = []
		return self._view_cache_team_scores[map_start_time]


	async def get_data_scores(self, map_start_time: any, sorting: ScoreSortingPresets) -> 'list[TeamPlayerScore]':
		lookup_matches = []
		if isinstance(map_start_time, int):
			lookup_matches.append(map_start_time)
		elif isinstance(map_start_time, list):
			lookup_matches = map_start_time
		else:
			logger.error("Unexpected type in get_data_scores: " + str(map_start_time))

		score_by_login = {}
		for start_time in lookup_matches:

			team_score_by_id = {}
			team_scores = await self.get_data_team_scores(start_time)
			for team_score in team_scores:
				team_score_by_id[team_score.team_id] = { 'score': team_score.score, 'name': team_score.name }

			player_scores = await self.get_data_player_scores(start_time)
			for player_score in player_scores:
				if player_score.login not in score_by_login:
					score_by_login[player_score.login] = {
						'score': 0,
						'score2': 0,
						'nickname': player_score.nickname,
						'country': player_score.country,
						'count': 0,
						'team': player_score.team,
						'team_name': '',
						'team_score': 0,
					}
					if team_score_by_id and player_score.team in team_score_by_id:
						score_by_login[player_score.login]['team_name'] = team_score_by_id[player_score.team]['name']
				if team_score_by_id and player_score.team in team_score_by_id:
					score_by_login[player_score.login]['team_score'] += team_score_by_id[player_score.team]['score']
				score_by_login[player_score.login]['score'] += player_score.score
				score_by_login[player_score.login]['score2'] += player_score.score2
				score_by_login[player_score.login]['count'] += 1

		scores = []	# type: list[TeamPlayerScore]
		for login, score_data in score_by_login.items():
			new_score = TeamPlayerScore(
				login,
				score_data['nickname'],
				score_data['country'],
				score_data['team'],
				score_data['team_name'],
				score_data['team_score'],
				score_data['score'],
				score_data['score2']
			)
			new_score.player_score_is_time = sorting in [ScoreSortingPresets.TIMEATTACK, ScoreSortingPresets.LAPS]
			new_score.count = score_data['count']
			scores.append(new_score)

		scores = TeamPlayerScore.sort_scores(scores, sorting)
		scores = TeamPlayerScore.update_placements(scores, sorting)

		return scores
