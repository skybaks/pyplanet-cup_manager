import logging
import datetime
from peewee import *

from pyplanet.apps.config import AppConfig
from pyplanet.apps.core.maniaplanet import callbacks as mp_signals
from pyplanet.apps.core.trackmania import callbacks as tm_signals
from pyplanet.apps.core.shootmania import callbacks as sm_signals
from pyplanet.contrib.setting import Setting
from pyplanet.contrib.command import Command
from pyplanet.utils import times

from .models import PlayerScore
from .views import MatchHistoryView, TextResultsView
from .app_types import ResultsViewParams, GenericPlayerScore

logger = logging.getLogger(__name__)

class CupManagerApp(AppConfig):
	game_dependencies = ['trackmania_next', 'trackmania', 'shootmania']
	app_dependencies = ['core.maniaplanet', 'core.trackmania', 'core.shootmania']
	_match_start_time = 0
	_match_map_name = ''
	_setting_match_history_amount = None
	_namespace = 'cup'
	_view_cache_matches = []
	_view_cache_scores = {}


	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._setting_match_history_amount = Setting(
			'match_history_amount', 'Amount of Saved Matches', Setting.CAT_BEHAVIOUR, type=int,
			description='Set this number to the number of previous matches you want to save in the database.',
			default=100
		)


	async def on_init(self):
		await super().on_init()


	async def on_start(self):
		self.context.signals.listen(tm_signals.scores, self._tm_signals_scores)
		self.context.signals.listen(mp_signals.map.map_start, self._mp_signals_map_map_start)
		self.context.signals.listen(mp_signals.map.map_end, self._mp_signals_map_map_end)
		self.context.signals.listen(sm_signals.base.scores, self._sm_signals_scores)

		await self.context.setting.register(self._setting_match_history_amount)

		await self.instance.command_manager.register(
			Command(command='matches', aliases=['m'], namespace=self._namespace, target=self._command_matches,
				description='Display saved match history.'),
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
		current_script = (await self.instance.mode_manager.get_current_script())
		current_script_lower = current_script.lower()
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
					rows = await PlayerScore.execute(
						PlayerScore.select().where(
							(PlayerScore.login == new_score.login) & (PlayerScore.map_start_time == self._match_start_time)
						)
					)
					if len(rows) > 0:
						logger.info("Entry exists, updating score")
						await PlayerScore.execute(
							PlayerScore.update(
								score=new_score.score,
								nickname=new_score.nickname,
								country=new_score.country,
								mode_script=current_script,
								map_name=self._match_map_name
							).where(
								(PlayerScore.login == new_score.login) & (PlayerScore.map_start_time == self._match_start_time)
							)
						)
					else:
						logger.info("No entry exists, creating score")
						await PlayerScore.execute(
							PlayerScore.insert(
								login=new_score.login,
								nickname=new_score.nickname,
								country=new_score.country,
								score=new_score.score,
								map_start_time=self._match_start_time,
								mode_script=current_script,
								map_name=self._match_map_name
							)
						)
					await self._invalidate_view_cache_matches()
					await self._invalidate_view_cache_scores(self._match_start_time)


	async def _handle_map_update(self, section: str):
		if section == 'OnStart' or section == 'MapStart':
			self._match_start_time = int(datetime.datetime.now().timestamp())
			self._match_map_name = self.instance.map_manager.current_map.name
		elif section == 'MapEnd':
			self._match_start_time = 0
			self._match_map_name = None
			await self._prune_match_history()
		else:
			logger.error('Unexpected section reached in _handle_map_update: \"' + section + '\"')
		logger.info(section)


	async def _prune_match_history(self):
		map_time_rows_query = await PlayerScore.execute(PlayerScore.select(fn.Distinct(PlayerScore.map_start_time)))
		map_times = [time.map_start_time for time in map_time_rows_query]
		map_times.sort()
		match_limit = await self._setting_match_history_amount.get_value()
		match_history_pruned = False
		while len(map_times) > match_limit:
			oldest_time = map_times[0]
			await PlayerScore.execute(PlayerScore.delete().where(PlayerScore.map_start_time == oldest_time))
			await self._invalidate_view_cache_scores(oldest_time)
			map_times.pop(0)
			logger.info('Removed records from match of time ' + datetime.datetime.fromtimestamp(oldest_time).strftime("%c") + '. new len is ' + str(len(map_times)))
			match_history_pruned = True
		if match_history_pruned:
			await self._invalidate_view_cache_matches()


	async def _command_matches(self, player, data, **kwargs):
		logger.info("Called the command: _command_matches")
		view = MatchHistoryView(self, player)
		await view.display(player=player.login)


	async def _command_current(self, player, data, **kwargs):
		logger.info("Called the command: _command_current")
		match_data = await self.get_data_matches()
		current_match = None
		for match in match_data:
			if match['map_start_time'] == self._match_start_time:
				current_match = ResultsViewParams(match['map_name'], match['map_start_time'], match['mode_script'])
				break
		else:
			logger.info("Current match data not found.")
			await self.instance.chat('$i$f00No scores found for current match.', player)
			return
		view = MatchHistoryView(self, player, current_match)
		await view.display(player=player.login)


	async def _invalidate_view_cache_matches(self):
		logger.info("_invalidate_view_cache_matches")
		self._view_cache_matches = []


	async def _invalidate_view_cache_scores(self, map_start_time: int=0):
		logger.info("_invalidate_view_cache_scores: " + str(map_start_time))
		if map_start_time == 0:
			self._view_cache_scores = {}
		elif map_start_time in self._view_cache_scores:
			self._view_cache_scores[map_start_time] = []


	async def _button_export(self, player, values, **kwargs):
		logger.info(f"Called _button_export {player.login}")
		view = TextResultsView(self, player, kwargs['view'].data['objects'])
		await view.display(player=player)


	async def get_data_matches(self) -> list:
		if not self._view_cache_matches:
			map_history_query = await PlayerScore.execute(PlayerScore.select(
				fn.Distinct(PlayerScore.map_start_time),
				PlayerScore.map_name,
				PlayerScore.mode_script
			).order_by(PlayerScore.map_start_time.desc()))
			for map in map_history_query:
				self._view_cache_matches.append({
					'selected': None,
					'map_name': map.map_name,
					'map_start_time_str': datetime.datetime.fromtimestamp(map.map_start_time).strftime("%c"),
					'map_start_time': map.map_start_time,
					'mode_script': map.mode_script,
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
			PlayerScore.nickname,
			PlayerScore.login,
			PlayerScore.score,
			PlayerScore.country
		).where(
			PlayerScore.map_start_time.in_(lookup_matches)
		))

		score_by_login = {}
		for player_score in map_scores_query:
			if player_score.login not in score_by_login:
				score_by_login[player_score.login] = { 'score': 0, 'nickname': player_score.nickname, 'country': player_score.country }
			score_by_login[player_score.login]['score'] += player_score.score
		scores = []
		for login, score_data in score_by_login.items():
			scores.append(GenericPlayerScore(login, score_data['nickname'], score_data['country'], score_data['score']))

		score_is_time = True if 'timeattack'in mode_script.lower() else False
		scores = sorted(scores, key=lambda x: x.score, reverse=not score_is_time)

		index = 1
		score_data = []
		for player_score in scores:
			score_data.append({
				'index': index,
				'nickname': player_score.nickname,
				'login': player_score.login,
				'score': player_score.score,
				'score_str': times.format_time(int(player_score.score)) if score_is_time else str(player_score.score),
				'country': player_score.country,
			})
			index += 1

		if isinstance(map_start_time, int) and (map_start_time not in self._view_cache_scores or not self._view_cache_scores[map_start_time]):
			self._view_cache_scores[map_start_time] = score_data

		return score_data

