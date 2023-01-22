import logging
from datetime import datetime
from peewee import *

from pyplanet.apps.core.maniaplanet import callbacks as mp_signals
from pyplanet.apps.core.trackmania import callbacks as tm_signals
from pyplanet.apps.core.shootmania import callbacks as sm_signals
from pyplanet.contrib.command import Command
from pyplanet.utils import style

from .models import PlayerScore, TeamScore, MatchInfo, CupInfo
from .views import MatchHistoryView, TextResultsView, AddRemoveCupMatchesView, ResultsView, GeneralResultsView, ScoreModeView
from .app_types import GenericPlayerScore, GenericTeamScore, TeamPlayerScore
from .score_mode import ScoreModeBase, SCORE_MODE
from .score_mode.mode_logic import get_sorting_from_mode

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
		self._view_cache_matches = []
		self._view_cache_scores = {}
		self._view_cache_team_scores = {}
		self._match_start_notify_list = []
		self._scores_update_notify_list = []

		AddRemoveCupMatchesView.set_get_data_method(self.get_data_matches)


	async def on_start(self) -> None:
		self.context.signals.listen(tm_signals.scores, self._tm_signals_scores)
		self.context.signals.listen(mp_signals.map.map_start, self._mp_signals_map_map_start)
		self.context.signals.listen(mp_signals.map.map_end, self._mp_signals_map_map_end)
		self.context.signals.listen(sm_signals.base.scores, self._tm_signals_scores)

		await self.instance.permission_manager.register('results_cup', 'Handle match results from cup_manager', app=self.app, min_level=2, namespace=self.app.namespace)

		await self.instance.command_manager.register(
			Command(command='matches', aliases=['m'], namespace=self.app.namespace, target=self._command_matches,
				description='Display saved match history.'),
			Command(command='matches', aliases=['m'], namespace=self.app.namespace, target=self._command_matches,
				admin=True, perms='cup:results_cup', description='Display saved match history.'),
		)

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
		logger.debug("Update TM scores complete in _tm_signals_scores")


	async def _mp_signals_map_map_start(self, time, count, restarted, map, **kwargs):
		await self._handle_map_update('MapStart')


	async def _mp_signals_map_map_end(self, map, **kwargs):
		await self._handle_map_update('MapEnd')


	async def _handle_team_score_update(self, team_scores: list) -> None:
		new_scores = []	# type: list[GenericTeamScore]
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
		new_scores: 'list[GenericPlayerScore]' = []
		for player_score in player_scores:
			try:
				new_score = GenericPlayerScore()
				new_score.login = player_score['login'] if 'login' in player_score else player_score['player'].login
				new_score.nickname = player_score['name'] if 'name' in player_score else player_score['player'].nickname

				new_score.country = 'World'
				try:
					new_score.country = player_score['player'].flow.zone.country
				except Exception as e:
					logger.error(f"Exception while accessing country for login \"{new_score.login}\", nickname \"{new_score.nick}\": {str(e)}")

				new_score.team = -1
				try:
					new_score.team = player_score['player'].flow.team_id
				except Exception as e:
					logger.error(f"Exception while accessing team_id for login \"{new_score.login}\", nickname \"{new_score.nick}\": {str(e)}")

				if 'timeattack' in current_script_lower:
					new_score.score = player_score['best_race_time'] if 'best_race_time' in player_score else player_score['bestracetime']
				elif 'laps' in current_script_lower:
					new_score.score = player_score['best_race_time'] if 'best_race_time' in player_score else player_score['bestracetime']
					new_score.score2 = len(player_score['best_race_checkpoints']) if 'best_race_checkpoints' in player_score else len(player_score['bestracecheckpoints'])
				else:
					new_score.score = player_score['map_points'] if 'map_points' in player_score else player_score['mappoints']
					new_score.score_match = player_score['match_points'] if 'match_points' in player_score else player_score['matchpoints']

				if new_score.score != -1:
					new_scores.append(new_score)

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
									score_match=new_score.score_match,
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
									score_match=new_score.score_match,
								)
							)
					except Exception as e:
						logger.error("Exception writing PlayerScore to database."
							+ f" map_start_time: {str(self._match_start_time)}, login: {str(new_score.login)},"
							+ f" nickname: {str(new_score.nickname)}, country: {str(new_score.country)}, score: {str(new_score.score)},"
							+ f" score2: {str(new_score.score2)}, team: {str(new_score.team)}, score_match: {str(new_score.score_match)}")
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
					medal_author=self.instance.map_manager.current_map.time_author,
					medal_gold=self.instance.map_manager.current_map.time_gold,
					medal_silver=self.instance.map_manager.current_map.time_silver,
					medal_bronze=self.instance.map_manager.current_map.time_bronze,
				))
			except Exception as e:
				logger.error("Exception while attempting to write map information to database."
					+ f" map_start_time: {str(self._match_start_time)}, mode_script: {str(current_mode_script)},"
					+ f" map_name: {str(self._match_map_name)}, map_uid: {str(current_map_uid)}, mx_id: {str(current_mx_id)},"
					+ f" medal_author: {str(self.instance.map_manager.current_map.time_author)},"
					+ f" medal_gold: {str(self.instance.map_manager.current_map.time_gold)},"
					+ f" medal_silver: {str(self.instance.map_manager.current_map.time_silver)},"
					+ f" medal_bronze: {str(self.instance.map_manager.current_map.time_bronze)}")
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

			match_data = await self.get_data_matches()
			for match in match_data:
				if match.map_start_time == ended_map_start_time:
					score_data = await self.get_data_scores(match.map_start_time, get_sorting_from_mode(str(match.mode_script)))
					await self.instance.chat(f'$ff0Saved $<$fff{str(len(score_data))}$> record(s) from map $<$fff{ended_map_map_name}$>')
					break
			else:
				await self.instance.chat(f'$ff0No records saved from map $<$fff{ended_map_map_name}$>')

		else:
			logger.error('Unexpected section reached in _handle_map_update: \"' + section + '\"')


	async def _command_matches(self, player, data, **kwargs):
		await self.open_view_match_history(player)


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


	async def _button_export(self, player, values, view: 'ResultsView | any', **kwargs):
		if view.scores_query:
			scores_data = await self.get_data_scores(view.scores_query, view.scores_sorting)

			match_info = []	# type: list[MatchInfo]
			all_match_data = await self.get_data_matches()
			for match_data_info in all_match_data:
				if (isinstance(view.scores_query, int) and match_data_info.map_start_time == view.scores_query) or (isinstance(view.scores_query, list) and match_data_info.map_start_time in view.scores_query):
					match_info.append(match_data_info)

			text_view = TextResultsView(
				self.app,
				player,
				scores_data,
				match_info,
				view.scores_sorting
			)

			if hasattr(view, 'cup_start_time'):
				cup_info = await self.app.active.get_data_specific_cup_info(view.cup_start_time)	# type: CupInfo
				text_view.cup_name = style.style_strip(cup_info.cup_name)
				text_view.cup_edition = 'Edition #' + str(cup_info.cup_edition)
				cup_keyname, cup_settings = await self.app.active.get_specific_cup_settings(cup_info.cup_key)
				if 'payout' in cup_settings:
					text_view.payout_key = cup_settings['payout']

			await text_view.display(player=player)


	async def register_match_start_notify(self, notify_method) -> None:
		if notify_method not in self._match_start_notify_list:
			self._match_start_notify_list.append(notify_method)


	async def register_scores_update_notify(self, notify_method) -> None:
		if notify_method not in self._scores_update_notify_list:
			self._scores_update_notify_list.append(notify_method)


	async def open_view_match_history(self, player) -> None:
		if await self.get_data_matches():
			view = MatchHistoryView(self.app, player)
			await view.display(player=player.login)
		else:
			await self.instance.chat('$f00No matches found', player)


	async def open_view_match_results(self, player, scores_query, scores_sorting) -> None:
		view = GeneralResultsView(self.app, player, scores_query, scores_sorting)
		await view.display(player=player)


	async def open_view_scoremode(self, player, target_view) -> None:
		async def scoremode_selected(scoremode, player):
			if scoremode in SCORE_MODE:
				target_view.scores_sorting = SCORE_MODE[scoremode]()
			else:
				target_view.scores_sorting = None
			await target_view.refresh(player=player)

		view = ScoreModeView(self.app, scoremode_selected)
		await view.display(player=player)


	async def get_current_match_start_time(self) -> int:
		return self._match_start_time


	async def get_data_matches(self) -> 'list[MatchInfo]':
		if not self._view_cache_matches:
			map_history_query = await MatchInfo.execute(MatchInfo.select().order_by(MatchInfo.map_start_time.desc()))
			if len(map_history_query) > 0:
				self._view_cache_matches = list(map_history_query)	# type: list[MatchInfo]
		return self._view_cache_matches


	async def get_data_specific_matches(self, matches: 'int | list[int]') -> 'list[MatchInfo]':
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


	async def get_data_scores(self, map_start_time: 'int | list[int]', sorting: ScoreModeBase) -> 'list[TeamPlayerScore]':
		lookup_matches = []
		if isinstance(map_start_time, int):
			lookup_matches.append(map_start_time)
		elif isinstance(map_start_time, list):
			lookup_matches = map_start_time
		else:
			logger.error("Unexpected type in get_data_scores: " + str(map_start_time))
		lookup_matches.sort()

		matches_scores = []	# type: list[list[TeamPlayerScore]]
		for start_time in lookup_matches:
			team_scores = await self.get_data_team_scores(start_time)
			team_lookup = {}	# type: dict[int, TeamScore]
			for team_score in team_scores:
				team_lookup[team_score.team_id] = team_score

			player_scores = await self.get_data_player_scores(start_time)
			team_player_scores = []	# type: list[TeamPlayerScore]
			for player_score in player_scores:
				new_score = TeamPlayerScore.from_player_score(player_score)
				if new_score.team_id in team_lookup:
					new_score.team_name = team_lookup[new_score.team_id].name
					new_score.team_score = team_lookup[new_score.team_id].score
				team_player_scores.append(new_score)
			matches_scores.append(team_player_scores)

		matches = await self.get_data_specific_matches(lookup_matches)
		matches = sorted(matches, key=lambda x: (x.map_start_time))

		scores = sorting.combine_scores(matches_scores, matches)
		scores = sorting.sort_scores(scores)
		scores = sorting.update_placements(scores)
		scores = sorting.update_score_is_time(scores)

		return scores
