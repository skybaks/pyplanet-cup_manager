import datetime

from pyplanet.views.generics.list import ManualListView

from ..app_types import ResultsViewParams


class MatchHistoryView(ManualListView):
	app = None

	title = 'Match History'
	icon_style = 'Icons128x128_1'
	icon_substyle = 'Browse'
	
	_player = None
	_results_view_mode = False
	_results_view_params = None
	_persist_matches_page = 0


	def __init__(self, app, player, map_score_instance: ResultsViewParams=None) -> None:
		super().__init__(self)
		self.app = app
		self.manager = app.context.ui
		self._player = player
		if map_score_instance:
			self._set_results_view_mode(map_score_instance)
		else:
			self._set_match_view_mode()


	async def get_fields(self) -> list:
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
					'width': 40,
					'type': 'label',
				},
				{
					'name': 'Score',
					'index': 'score_str',
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
					'width': 40,
					'type': 'label'
				},
			]
		return fields


	async def get_buttons(self) -> list:
		buttons = []
		if self._results_view_mode:
			buttons.append({
				'title': 'Back',
				'width': 30,
				'action': self._button_back,
			})
		return buttons


	async def get_data(self) -> list:
		items = []
		if self._results_view_mode:
			items = await self.app.get_data_scores(self._results_view_params.map_start_time, self._results_view_params.mode_script)

		if not items:
			self._results_view_mode = False
			self._results_view_params = None
			self._persist_matches_page = 0
			self._set_match_view_mode()
			items = await self.app.get_data_matches()
		return items


	async def _action_view_match(self, player, values, instance, **kwargs):
		self._set_results_view_mode(ResultsViewParams(instance['map_name'], instance['map_start_time'], instance['mode_script']))
		await self.refresh(player=self._player)


	async def _button_back(self, player, values, **kwargs):
		self._set_match_view_mode()
		await self.refresh(player=self._player)


	def _set_match_view_mode(self):
		self._results_view_params = None
		self._results_view_mode = False
		if self._persist_matches_page != 0:
			self.page = self._persist_matches_page
			self._persist_matches_page = 0
		self.title = 'Match History'


	def _set_results_view_mode(self, results_view_params: ResultsViewParams):
		self._results_view_params = results_view_params
		self._results_view_mode = True
		self._persist_matches_page = self.page
		self.page = 1
		self.title = '$<' + self._results_view_params.map_name + '$> / ' + datetime.datetime.fromtimestamp(self._results_view_params.map_start_time).strftime("%c") + ' / ' + self._results_view_params.mode_script

