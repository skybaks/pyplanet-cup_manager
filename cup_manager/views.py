from peewee import *
import datetime

from pyplanet.views.generics.list import ManualListView

from .models import PlayerScore

class MatchHistoryView(ManualListView):
	app = None

	title = 'Cup Manager: Match History'
	icon_style = 'Icons128x128_1'
	icon_substyle = 'Browse'
	
	_player = None
	_cache_matches = []
	_cache_results = {}
	_show_results_time = 0
	_results_view_mode = False
	_results_view_params = {}


	def __init__(self, app, player):
		super().__init__(self)
		self.app = app
		self.manager = app.context.ui
		self._player = player


	async def get_fields(self):
		fields = []
		if self._results_view_mode:
			fields = [
				{
					'name': '#',
					'index': 'index',
					'sorting': True,
					'searching': False,
					'width': 10,
					'type': 'label',
				},
				{
					'name': 'Nickname',
					'index': 'nickname',
					'sorting': False,
					'searching': False,
					'width': 80,
					'type': 'label',
				},
				{
					'name': 'Login',
					'index': 'login',
					'sorting': False,
					'searching': True,
					'width': 30,
					'type': 'label',
				},
				{
					'name': 'Score',
					'index': 'score',
					'sorting': True,
					'searching': False,
					'width': 20,
					'type': 'label',
				},
				{
					'name': 'Country',
					'index': 'country',
					'sorting': True,
					'searching': True,
					'width': 30,
					'type': 'label',
				},
			]
		else:
			fields =[
				{
					'name': 'Map',
					'index': 'map_name',
					'sorting': True,
					'searching': True,
					'width': 80,
					'type': 'label',
					'action': self._action_view_match
				},
				{
					'name': 'Start Time',
					'index': 'map_start_time_str',
					'sorting': True,
					'searching': True,
					'width': 40,
					'type': 'label'
				},
				{
					'name': 'Mode',
					'index': 'mode_script',
					'sorting': True,
					'searching': True,
					'width': 30,
					'type': 'label'
				},
			]
		return fields


	async def get_buttons(self):
		buttons = []
		if self._results_view_mode:
			buttons.append({
				'title': 'Back',
				'width': 30,
				'action': self._button_back,
			})
		return buttons


	async def get_data(self):
		items = []
		if self._results_view_mode:
			if self._results_view_params['map_start_time'] not in self._cache_results:
				map_scores = await PlayerScore.execute(PlayerScore.select(
					PlayerScore.nickname,
					PlayerScore.login,
					PlayerScore.score,
					PlayerScore.country
				).where(PlayerScore.map_start_time == self._results_view_params['map_start_time']).order_by(PlayerScore.score.asc()))
				self._cache_results[self._results_view_params['map_start_time']] = []
				index = 1
				for player_score in map_scores:
					self._cache_results[self._results_view_params['map_start_time']].append({
						'index': index,
						'nickname': player_score.nickname,
						'login': player_score.login,
						'score': player_score.score,
						'country': player_score.country,
					})
					index += 1
			items = self._cache_results[self._results_view_params['map_start_time']]
		else:
			if not self._cache_matches:
				map_history = await PlayerScore.execute(PlayerScore.select(
					fn.Distinct(PlayerScore.map_start_time),
					PlayerScore.map_name,
					PlayerScore.mode_script
				).order_by(PlayerScore.map_start_time.desc()))
				self._cache_matches = []
				for map in map_history:
					self._cache_matches.append({
						'map_name': map.map_name,
						'map_start_time_str': datetime.datetime.fromtimestamp(map.map_start_time).strftime("%c"),
						'map_start_time': map.map_start_time,
						'mode_script': map.mode_script,
					})
			items = self._cache_matches
		return items


	async def destroy(self):
		await super().destroy()
		self._cache_matches = []
		self._cache_results = {}
		self._show_results_time = 0


	def destroy_sync(self):
		super().destroy_sync()
		self._cache_matches = []
		self._cache_results = {}
		self._show_results_time = 0


	async def _action_view_match(self, player, values, instance, **kwargs):
		self._results_view_params = {
			'map_start_time': instance['map_start_time'],
			'map_name': instance['map_name'],
		}
		self._results_view_mode = True
		await self.refresh(player=self._player)


	async def _button_back(self, player, values, **kwargs):
		self._results_view_params = {}
		self._results_view_mode = False
		await self.refresh(player=self._player)

