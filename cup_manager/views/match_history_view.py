import datetime
from inspect import iscoroutinefunction, isfunction
import logging

from pyplanet.views.generics.list import ManualListView

from ..app_types import ResultsViewParams

logger = logging.getLogger(__name__)

class MatchHistoryView(ManualListView):
	app = None

	title = 'Match History'
	icon_style = 'Icons128x128_1'
	icon_substyle = None

	custom_results_view_buttons = []

	def __init__(self, app, player, map_score_instance: ResultsViewParams=None) -> None:
		super().__init__(self)
		self.app = app
		self.manager = app.context.ui
		self.player = player
		self.results_view_show_score2 = False
		self.scores_query = None
		self.results_view_params = None
		self._results_view_mode = False
		self._persist_matches_page = 0
		self._selected_matches = []
		self._selected_matches_mode = False
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
					'sorting': False,
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
					'searching': False,
					'width': 50,
					'type': 'label',
				},
				{
					'name': 'Score',
					'index': 'score_str',
					'sorting': False,
					'searching': False,
					'width': 20,
					'type': 'label',
				},
			]

			if self.results_view_show_score2:
				fields.append(
					{
						'name': 'Score2',
						'index': 'score2_str',
						'sorting': False,
						'searching': False,
						'width': 20,
						'type': 'label',
					}
				)

			fields.append(
				{
					'name': 'Country',
					'index': 'country',
					'sorting': False,
					'searching': False,
					'width': 30,
					'type': 'label',
				},
			)
		else:
			fields =[
				{
					'name': '',
					'index': 'selected',
					'sorting': False,
					'searching': False,
					'width': 6,
					'type': 'label',
					'action': self._action_match_select
				},
				{
					'name': 'Map',
					'index': 'map_name',
					'sorting': False,
					'searching': False,
					'width': 80,
					'type': 'label',
					'action': self._action_view_match
				},
				{
					'name': 'Start Time',
					'index': 'map_start_time_str',
					'sorting': False,
					'searching': False,
					'width': 40,
					'type': 'label'
				},
				{
					'name': 'Mode',
					'index': 'mode_script',
					'sorting': False,
					'searching': False,
					'width': 50,
					'type': 'label'
				},
			]
		return fields


	async def get_buttons(self) -> list:
		buttons = []
		if self._results_view_mode:
			buttons.append({
				'title': 'Back',
				'width': 25,
				'action': self._button_back,
			})
			for custom_button in self.custom_results_view_buttons:
				if iscoroutinefunction(custom_button['visible']):
					if await custom_button['visible'](player=self.player, view=self):
						buttons.append(custom_button)

				elif isfunction(custom_button['visible']):
					if custom_button['visible'](player=self.player, view=self):
						buttons.append(custom_button)

				elif custom_button['visible']:
					buttons.append(custom_button)
		else:
			if self._selected_matches:
				buttons.append({
					'title': 'Sum Sel.',
					'width': 25,
					'action': self._button_calculate_results
				})
				buttons.append({
					'title': 'Clear Sel.',
					'width': 25,
					'action': self._button_clear_selection
				})
		return buttons


	async def get_data(self) -> list:
		items = []
		if self._results_view_mode:
			self.scores_query = self._selected_matches if self._selected_matches_mode else self.results_view_params.map_start_time
			scores = await self.app.get_data_scores(self.scores_query, self.results_view_params.mode_script)
			index = 1
			for player_score in scores:
				items.append({
					'index': index,
					'login': player_score.login,
					'nickname': player_score.nickname,
					'country': player_score.country,
					'score': player_score.score,
					'score_str': player_score.score_str,
					'score2': player_score.score2,
					'score2_str': player_score.score2_str,
				})
				index += 1

		if not items:
			self.scores_query = None
			self.results_view_params = None
			self._results_view_mode = False
			self._persist_matches_page = 0
			self._set_match_view_mode()
			maps = await self.app.get_data_matches()
			for map in maps:
				items.append({
					'selected': '' if map.map_start_time in self._selected_matches else '',
					'map_start_time_str': datetime.datetime.fromtimestamp(map.map_start_time).strftime("%c"),
					'map_start_time': map.map_start_time,
					'mode_script': map.mode_script,
					'map_name': map.map_name,
					'map_uid': map.map_uid,
					'mx_id': map.mx_id,
				})
		return items


	async def close(self, player, *args, **kwargs):
		return await super().close(player, *args, **kwargs)


	@classmethod
	def add_button(cls, target, name, visible, width):
		cls.custom_results_view_buttons.append({
			'action': target,
			'title': name,
			'width': width,
			'visible': visible,
		})


	async def _action_view_match(self, player, values, instance, **kwargs):
		self._selected_matches_mode = False
		self._set_results_view_mode(ResultsViewParams(instance['map_name'], instance['map_start_time'], instance['mode_script']))
		await self.refresh(player=player)


	async def _action_match_select(self, player, values, instance, **kwargs):
		if instance['map_start_time'] in self._selected_matches:
			self._selected_matches.remove(instance['map_start_time'])
		else:
			self._selected_matches.append(instance['map_start_time'])
		await self.refresh(player=player)


	async def _button_back(self, player, values, **kwargs):
		self._selected_matches_mode = False
		self._set_match_view_mode()
		await self.refresh(player=player)


	async def _button_calculate_results(self, player, values, **kwargs):
		self._selected_matches_mode = True
		matches = await self.app.get_data_matches()
		mode_script = None
		for match in matches:
			if match.map_start_time in self._selected_matches:
				mode_script = match.mode_script
				break
		self._set_results_view_mode(ResultsViewParams('', -1, mode_script))
		await self.refresh(player=player)


	async def _button_clear_selection(self, player, values, **kwargs):
		self._selected_matches_mode = False
		self._selected_matches = []
		await self.refresh(player=player)


	def _set_match_view_mode(self):
		self.icon_substyle = 'Statistics'
		self.results_view_params = None
		self._results_view_mode = False
		if self._persist_matches_page != 0:
			self.page = self._persist_matches_page
			self._persist_matches_page = 0
		self.title = 'Match History'


	def _set_results_view_mode(self, results_view_params: ResultsViewParams):
		self.icon_substyle = 'Rankings'
		self.results_view_show_score2 = 'laps' in results_view_params.mode_script.lower()
		self.results_view_params = results_view_params
		self._results_view_mode = True
		self._persist_matches_page = self.page
		self.page = 1
		if self._selected_matches_mode:
			self.title = 'Selected Matches Results'
		else:
			self.title = '$<' + self.results_view_params.map_name + '$> / ' + datetime.datetime.fromtimestamp(self.results_view_params.map_start_time).strftime("%c")

