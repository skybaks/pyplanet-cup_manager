import logging
import datetime
from peewee import *

from pyplanet.apps.core.maniaplanet import callbacks as mp_signals
from pyplanet.apps.core.trackmania import callbacks as tm_signals
from pyplanet.apps.core.shootmania import callbacks as sm_signals
from pyplanet.contrib.setting import Setting
from pyplanet.contrib.command import Command
from pyplanet.utils import times

from .models import PlayerScore, MatchInfo
from .views import MatchHistoryView, TextResultsView
from .app_types import GenericPlayerScore

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
		self._match_info_created = False
		self._setting_match_history_amount = None
		self._view_cache_matches = []
		self._view_cache_scores = {}

		self._setting_match_history_amount = Setting(
			'match_history_amount', 'Amount of Saved Matches', Setting.CAT_BEHAVIOUR, type=int,
			description='Set this number to the number of previous matches you want to save in the database.',
			default=100
		)


	async def on_start(self) -> None:
		self.context.signals.listen(tm_signals.scores, self._tm_signals_scores)
		self.context.signals.listen(mp_signals.map.map_start, self._mp_signals_map_map_start)
		self.context.signals.listen(mp_signals.map.map_end, self._mp_signals_map_map_end)
		self.context.signals.listen(sm_signals.base.scores, self._sm_signals_scores)

		await self.context.setting.register(self._setting_match_history_amount)

		await self.instance.command_manager.register(
			Command(command='matches', aliases=['m'], namespace=self.app.namespace, target=self._command_matches,
				description='Display saved match history.'),
			Command(command='matches', aliases=['m'], namespace=self.app.namespace, target=self._command_matches,
				admin=True, description='Display saved match history.'),
		)

		MatchHistoryView.add_button(self._button_export, 'Export', 30)

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
			await self._handle_score_update(scores['players'])


	async def _tm_signals_scores(self, players, teams, winner_team, use_teams, winner_player, section, **kwargs):
		if section == 'PreEndRound':
			# PreEndRound score callback shows round_points before they are added to match_points. For simplicity I only care about match_points.
			return
		await self._handle_score_update(players)


	async def _sm_signals_scores(self, players, teams, winner_team, use_teams, winner_player, section, **kwargs):
		if section == 'PreEndRound':
			# PreEndRound score callback shows round_points before they are added to match_points. For simplicity I only care about match_points.
			return
		await self._handle_score_update(players)


	async def _mp_signals_map_map_start(self, time, count, restarted, map, **kwargs):
		await self._handle_map_update('MapStart')


	async def _mp_signals_map_map_end(self, map, **kwargs):
		await self._handle_map_update('MapEnd')


	async def _handle_score_update(self, player_scores: list):
		current_script_lower = (await self.instance.mode_manager.get_current_script()).lower()
		new_scores = []
		for player_score in player_scores:
			try:
				new_score_login = player_score['login'] if 'login' in player_score else player_score['player'].login
				new_score_nick = player_score['name'] if 'name' in player_score else player_score['player'].nickname
				new_score_country = player_score['player'].flow.zone.country if 'player' in player_score else None

				if 'timeattack' in current_script_lower:
					new_score_score = player_score['best_race_time'] if 'best_race_time' in player_score else player_score['bestracetime']
					if new_score_score != -1:
						new_scores.append(GenericPlayerScore(new_score_login, new_score_nick, new_score_country, new_score_score))

				elif 'laps' in current_script_lower:
					new_score_score = player_score['best_race_time'] if 'best_race_time' in player_score else player_score['bestracetime']
					new_score_score2 = len(player_score['best_race_checkpoints']) if 'best_race_checkpoints' in player_score else len(player_score['bestracecheckpoints'])
					if new_score_score != -1:
						new_scores.append(GenericPlayerScore(new_score_login, new_score_nick, new_score_country, new_score_score, new_score_score2))

				else:
					new_score_score = player_score['map_points'] if 'map_points' in player_score else player_score['mappoints']
					if new_score_score != -1:
						new_scores.append(GenericPlayerScore(new_score_login, new_score_nick, new_score_country, new_score_score))

			except Exception as e:
				logger.error(f"Exception while recording scores for following player_score object: {str(player_score)}")
				logger.error(str(e))

		if new_scores:
			for new_score in new_scores:
				logger.info(new_score)
				if self._match_start_time != 0:
					await self._create_match_info()

					if new_score.login in self._match_players_scored:
						logger.info("Entry exists, updating score")
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
						logger.info("No entry exists, creating score")
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
					await self._invalidate_view_cache_scores(self._match_start_time)


	async def _create_match_info(self) -> None:
		if not self._match_info_created:
			logger.info("Current match data does not exist, creating")
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

			await MatchInfo.execute(MatchInfo.insert(
				map_start_time=self._match_start_time,
				mode_script=current_mode_script,
				map_name=self._match_map_name,
				map_uid=current_map_uid,
				mx_id=current_mx_id,
			))
			await self._invalidate_view_cache_matches()


	async def _handle_map_update(self, section: str):
		if section == 'OnStart' or section == 'MapStart':
			self._match_start_time = int(datetime.datetime.now().timestamp())
			self._match_map_name = self.instance.map_manager.current_map.name
			self._match_players_scored = []
			self._match_info_created = False

		elif section == 'MapEnd':
			ended_map_start_time = self._match_start_time
			ended_map_map_name = self._match_map_name
			self._match_start_time = 0
			self._match_map_name = None
			self._match_players_scored = []
			self._match_info_created = False

			await self._prune_match_history()
			match_data = await self.get_data_matches()
			for match in match_data:
				if match['map_start_time'] == ended_map_start_time:
					score_data = await self.get_data_scores(match['map_start_time'], match['mode_script'])
					await self.instance.chat(f'$i$fffSaved {str(len(score_data))} record(s) from map $<{ended_map_map_name}$>.')
					break
			else:
				await self.instance.chat(f'$i$fffNo records saved from map $<{ended_map_map_name}$>.')

		else:
			logger.error('Unexpected section reached in _handle_map_update: \"' + section + '\"')
		logger.debug(section)


	async def _prune_match_history(self):
		map_time_rows_query = await PlayerScore.execute(PlayerScore.select(fn.Distinct(PlayerScore.map_start_time)))
		map_times = [time.map_start_time for time in map_time_rows_query]
		map_times.sort()
		match_limit = await self._setting_match_history_amount.get_value()

		while len(map_times) > match_limit:
			oldest_time = map_times[0]
			await PlayerScore.execute(PlayerScore.delete().where(PlayerScore.map_start_time == oldest_time))
			await MatchInfo.execute(MatchInfo.delete().where(MatchInfo.map_start_time == oldest_time))
			await self._invalidate_view_cache_scores(oldest_time)
			await self._invalidate_view_cache_matches()
			map_times.pop(0)
			logger.debug('Removed records from match of time ' + datetime.datetime.fromtimestamp(oldest_time).strftime("%c") + '. new len is ' + str(len(map_times)))


	async def _command_matches(self, player, data, **kwargs):
		logger.debug("Called the command: _command_matches")
		if await self.get_data_matches():
			view = MatchHistoryView(self, player)
			await view.display(player=player.login)
		else:
			await self.instance.chat('$i$f00No matches found.', player)


	async def _invalidate_view_cache_matches(self):
		logger.debug("_invalidate_view_cache_matches")
		self._view_cache_matches = []


	async def _invalidate_view_cache_scores(self, map_start_time: int=0):
		logger.debug("_invalidate_view_cache_scores: " + str(map_start_time))
		if map_start_time == 0:
			self._view_cache_scores = {}
		elif map_start_time in self._view_cache_scores:
			del self._view_cache_scores[map_start_time]


	async def _button_export(self, player, values, view, **kwargs):
		logger.debug(f"Called _button_export {player.login}")
		if view.scores_query:
			scores_data = await self.get_data_scores(view.scores_query, view.results_view_params.mode_script)
			text_view = TextResultsView(self, player, scores_data, view.results_view_show_score2)
			await text_view.display(player=player)


	async def get_data_matches(self) -> list:
		if not self._view_cache_matches:
			map_history_query = await MatchInfo.execute(MatchInfo.select(
				MatchInfo.map_start_time,
				MatchInfo.mode_script,
				MatchInfo.map_name,
				MatchInfo.map_uid,
				MatchInfo.mx_id,
			).order_by(MatchInfo.map_start_time.desc()))
			for map in map_history_query:
				self._view_cache_matches.append({
					'selected': None,
					'map_start_time_str': datetime.datetime.fromtimestamp(map.map_start_time).strftime("%c"),
					'map_start_time': map.map_start_time,
					'mode_script': map.mode_script,
					'map_name': map.map_name,
					'map_uid': map.map_uid,
					'mx_id': map.mx_id,
				})
		return self._view_cache_matches


	async def get_data_scores(self, map_start_time, mode_script: str) -> list:
		lookup_matches = []
		if isinstance(map_start_time, int):
			if map_start_time in self._view_cache_scores and self._view_cache_scores[map_start_time]:
				return self._view_cache_scores[map_start_time]
			lookup_matches.append(map_start_time)
		elif isinstance(map_start_time, list):
			lookup_matches = map_start_time

		map_scores_query = await PlayerScore.execute(PlayerScore.select(
			PlayerScore.login,
			PlayerScore.nickname,
			PlayerScore.country,
			PlayerScore.score,
			PlayerScore.score2,
			# TODO: Design team score handling
			PlayerScore.team,
		).where(
			PlayerScore.map_start_time.in_(lookup_matches)
		))

		score_by_login = {}
		for player_score in map_scores_query:
			if player_score.login not in score_by_login:
				score_by_login[player_score.login] = { 'score': 0, 'score2': 0, 'nickname': player_score.nickname, 'country': player_score.country }
			score_by_login[player_score.login]['score'] += player_score.score
			score_by_login[player_score.login]['score2'] += player_score.score2
		scores = []
		for login, score_data in score_by_login.items():
			scores.append(GenericPlayerScore(login, score_data['nickname'], score_data['country'], score_data['score'], score_data['score2']))

		score_is_time = True if 'timeattack'in mode_script.lower() or 'laps' in mode_script.lower() else False
		scores = sorted(scores, key=lambda x: (-x.score2, x.score), reverse=not score_is_time)

		index = 1
		score_data = []
		for player_score in scores:
			score_data.append({
				'index': index,
				'nickname': player_score.nickname,
				'login': player_score.login,
				'score': player_score.score,
				'score_str': times.format_time(int(player_score.score)) if score_is_time else str(player_score.score),
				'score2': player_score.score2,
				'score2_str': str(player_score.score2),
				'country': player_score.country,
			})
			index += 1

		if isinstance(map_start_time, int) and (map_start_time not in self._view_cache_scores or not self._view_cache_scores[map_start_time]):
			self._view_cache_scores[map_start_time] = score_data

		return score_data
