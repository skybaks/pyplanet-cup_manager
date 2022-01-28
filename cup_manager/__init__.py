from pyplanet.apps.config import AppConfig
from pyplanet.apps.core.maniaplanet import callbacks as mp_signals
from pyplanet.apps.core.trackmania import callbacks as tm_signals
import logging


class CupManagerApp(AppConfig):
	game_dependencies = ['trackmania_next', 'trackmania', 'shootmania']
	app_dependencies = ['core.maniaplanet', 'core.trackmania', 'core.shootmania']
	_logger = None


	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self._logger = logging.getLogger(__name__)


	async def on_init(self):
		await super().on_init()


	async def on_start(self):
		self.context.signals.listen(tm_signals.scores, self._tm_signals_scores)
		self.context.signals.listen(mp_signals.map.map_start, self._mp_signals_map_map_start)
		self.context.signals.listen(mp_signals.map.map_end, self._mp_signals_map_map_end)

		await self._handle_map_update('OnStart')

		scores = None
		try:
			scores = await self.instance.gbx('Trackmania.GetScores')
		except:
			pass

		if scores:
			await self._handle_score_update(scores['players'])


	async def _tm_signals_scores(self, players, teams, winner_team, use_teams, winner_player, section, **kwargs):
		"""
		Score events for rounds: (tested in lagoon)
			PreEndRound		-> round_points before being added to match_points
			EndRound		-> match_points summed to include round_points
			EndMap			-> match_points totaled
			EndMatch		-> match_points totaled
		"""
		if section == 'PreEndRound':
			# PreEndRound score callback shows round_points before they are added to match_points. For simplicity I only care about match_points.
			return
		await self._handle_score_update(players)


	async def _mp_signals_map_map_start(self, time, count, restarted, map, **kwargs):
		await self._handle_map_update('MapStart')


	async def _mp_signals_map_map_end(self, map, **kwargs):
		await self._handle_map_update('MapEnd')


	async def _handle_score_update(self, player_scores):
		current_script = (await self.instance.mode_manager.get_current_script()).lower()
		# If in timeattack, use best race time as score. In all other cases use points.
		new_score = {}
		if 'timeattack' in current_script or 'trackmania/tm_timeattack_online' in current_script:
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


	async def _handle_map_update(self, section):
		map_info = {
			'uid': self.instance.map_manager.current_map.uid,
			'name': self.instance.map_manager.current_map.name
		}
		self._logger.info(section)
		self._logger.info(map_info)

