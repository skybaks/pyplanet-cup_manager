import logging
import datetime
from peewee import *

from pyplanet.apps.config import AppConfig
from pyplanet.apps.core.maniaplanet import callbacks as mp_signals
from pyplanet.apps.core.trackmania import callbacks as tm_signals
from pyplanet.contrib.setting import Setting

from .models import PlayerScore


class CupManagerApp(AppConfig):
	game_dependencies = ['trackmania_next', 'trackmania', 'shootmania']
	app_dependencies = ['core.maniaplanet', 'core.trackmania', 'core.shootmania']
	_logger = None
	_match_start_time = 0
	_match_map_name = ''
	_setting_match_history_amount = None

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._logger = logging.getLogger(__name__)
		self._setting_match_history_amount = Setting(
			'match_history_amount', 'Amount of Saved Matches', Setting.CAT_BEHAVIOUR, type=int,
			description='Set this number to the number of previous matches you want to save in the database.',
			default=20
		)


	async def on_init(self):
		await super().on_init()


	async def on_start(self):
		self.context.signals.listen(tm_signals.scores, self._tm_signals_scores)
		self.context.signals.listen(mp_signals.map.map_start, self._mp_signals_map_map_start)
		self.context.signals.listen(mp_signals.map.map_end, self._mp_signals_map_map_end)

		await self.context.setting.register(self._setting_match_history_amount)

		await self._handle_map_update('OnStart')

		scores = None
		try:
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


	async def _mp_signals_map_map_start(self, time, count, restarted, map, **kwargs):
		await self._handle_map_update('MapStart')


	async def _mp_signals_map_map_end(self, map, **kwargs):
		await self._handle_map_update('MapEnd')


	async def _handle_score_update(self, player_scores):
		current_script = (await self.instance.mode_manager.get_current_script())
		current_script_lower = current_script.lower()
		# If in timeattack, use best race time as score. In all other cases use points.
		new_score = {}
		if 'timeattack' in current_script_lower or 'trackmania/tm_timeattack_online' in current_script_lower:
			for player_score in player_scores:
				if 'best_race_time' in player_score and player_score['best_race_time'] != -1:
					new_score = {
						'login': player_score['player'].login,
						'nickname': player_score['player'].nickname,
						'country': player_score['player'].flow.zone.country,
						'score': player_score['best_race_time']
					}
				elif 'bestracetime' in player_score and player_score['bestracetime'] != -1:
					new_score = {
						'login': player_score['login'],
						'nickname': player_score['name'],
						'country': None,	# TODO: Is this different? How and why?
						'score': player_score['bestracetime']
					}
		else:
			for player_score in player_scores:
				if 'map_points' in player_score and player_score['map_points'] != -1:
					new_score = {
						'login': player_score['player'].login,
						'nickname': player_score['player'].nickname,
						'country': player_score['player'].flow.zone.country,
						'score': player_score['map_points']
					}
				elif 'mappoints' in player_score and player_score['mappoints'] != -1:
					new_score = {
						'login': player_score['login'],
						'nickname': player_score['name'],
						'country': None,	# TODO: Is this different? How and why?
						'score': player_score['mappoints']
					}
		if new_score:
			self._logger.info(new_score)
			if self._match_start_time:
				self._logger.info("Valid match start time exists")
				rows = await PlayerScore.execute(
					PlayerScore.select().where(
						PlayerScore.login == new_score['login'] and PlayerScore.map_start_time == self._match_start_time
					)
				)
				if len(rows) > 0:
					self._logger.info("Entry exists, updating score")
					await PlayerScore.execute(
						PlayerScore.update(
							score=new_score['score'],
							nickname=new_score['nickname'],
							country=new_score['country'],
							mode_script=current_script,
							map_name=self._match_map_name
						).where(
							PlayerScore.login == new_score['login'] and PlayerScore.map_start_time == self._match_start_time
						)
					)
				else:
					self._logger.info("No entry exists, creating score")
					await PlayerScore(
						login=new_score['login'],
						nickname=new_score['nickname'],
						country=new_score['country'],
						score=new_score['score'],
						map_start_time=self._match_start_time,
						mode_script=current_script,
						map_name=self._match_map_name
					).save()


	async def _handle_map_update(self, section):
		if section == 'OnStart' or section == 'MapStart':
			self._match_start_time = int(datetime.datetime.now().timestamp())
			self._match_map_name = self.instance.map_manager.current_map.name
		elif section == 'MapEnd':
			self._match_start_time = 0
			self._match_map_name = None
			await self._prune_match_history()
		else:
			self._logger.error('Unexpected section reached in _handle_map_update: \"' + section + '\"')
		self._logger.info(section)


	async def _prune_match_history(self):
		map_time_rows_query = await PlayerScore.execute(PlayerScore.select(fn.Distinct(PlayerScore.map_start_time)))
		map_times = [time.map_start_time for time in map_time_rows_query]
		map_times.sort()
		match_limit = await self._setting_match_history_amount.get_value()
		while len(map_times) > match_limit:
			oldest_time = map_times[0]
			await PlayerScore.execute(PlayerScore.delete().where(PlayerScore.map_start_time == oldest_time))
			map_times.pop(0)
			self._logger.info('Removed records from match of time ' + datetime.datetime.fromtimestamp(oldest_time).strftime("%c") + '. new len is ' + str(len(map_times)))

