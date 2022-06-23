import datetime
from inspect import iscoroutinefunction, isfunction
import logging

from pyplanet.views.generics.list import ManualListView

from ..app_types import ScoreSortingPresets

logger = logging.getLogger(__name__)

class MatchHistoryView(ManualListView):
	app = None
	title = 'Match History'
	icon_style = 'Icons128x128_1'
	icon_substyle = None

	custom_results_view_buttons = []

	def __init__(self, app, player, init_query:'list[int]'=[], init_results_view: bool=False, init_sorting: ScoreSortingPresets=ScoreSortingPresets.UNDEFINED, init_title: str=None) -> None:
		super().__init__(self)
		self.app = app
		self.manager = app.context.ui
		self.player = player
		self.provide_search = False

		self.scores_query = init_query
		self.scores_sorting = init_sorting
		self.results_view_mode = init_results_view
		self.persist_matches_page = 0

		if self.results_view_mode:
			self._set_results_view_mode(init_title)
		else:
			self._set_match_view_mode()


	async def get_fields(self) -> 'list[dict[str, any]]':
		fields = []
		if self.results_view_mode:
			nickname_width = 105
			score2_width = 20
			team_width = 20

			if self.get_score2_visible():
				nickname_width -= score2_width
			if self.get_team_score_visible():
				nickname_width -= team_width

			fields += [
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
					'width': nickname_width,
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
			]
			if self.get_team_score_visible():
				fields.append(
					{
						'name': 'Team',
						'index': 'team_score_str',
						'sorting': False,
						'searching': False,
						'width': team_width,
						'type': 'label',
					}
				)
			fields.append(
				{
					'name': 'Score',
					'index': 'player_score_str',
					'sorting': False,
					'searching': False,
					'width': 20,
					'type': 'label',
				},
			)
			if self.get_score2_visible():
				fields.append(
					{
						'name': 'Score2',
						'index': 'player_score2_str',
						'sorting': False,
						'searching': False,
						'width': score2_width,
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
			fields = [
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


	async def get_buttons(self) -> 'list[dict[str, any]]':
		buttons = []
		if self.results_view_mode:
			buttons.append(
				{
					'title': 'Back',
					'width': 25,
					'action': self._button_back,
				},
			)
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
			buttons += [
				{
					'title': 'Sum Sel.',
					'width': 25,
					'action': self._button_calculate_results,
				},
				{
					'title': 'Clear Sel.',
					'width': 25,
					'action': self._button_clear_selection,
				},
			]
		return buttons


	async def get_data(self) -> 'list[dict[str, any]]':
		items = []
		if self.results_view_mode:
			scores = await self.app.results.get_data_scores(self.scores_query, self.scores_sorting)
			index = 1
			for player_score in scores:
				highlight = '$0cf' if player_score.login == self.player.login else ''
				items.append(
					{
						'index': highlight + str(index),
						'login': highlight + str(player_score.login),
						'nickname': highlight + str(player_score.nickname),
						'country': highlight + str(player_score.country),
						'player_score_str': highlight + str(player_score.player_score_str),
						'player_score2_str': highlight + str(player_score.player_score2_str),
						'team_score_str': highlight + str(player_score.team_score_str),
					}
				)
				index += 1

		if not items:
			self.results_view_mode = False
			self.persist_matches_page = 0
			self._set_match_view_mode()
			maps = await self.app.results.get_data_matches()
			for map in maps:
				items.append({
					'selected': '' if map.map_start_time in self.scores_query else '',
					'map_start_time_str': datetime.datetime.fromtimestamp(map.map_start_time).strftime("%c"),
					'map_start_time': map.map_start_time,
					'mode_script': map.mode_script,
					'map_name': map.map_name,
					'map_uid': map.map_uid,
					'mx_id': map.mx_id,
				})

		return items


	@classmethod
	def add_button(cls, target, name, visible, width) -> None:
		cls.custom_results_view_buttons.append({
			'action': target,
			'title': name,
			'width': width,
			'visible': visible,
		})


	async def _action_view_match(self, player, values, instance, **kwargs) -> None:
		self.scores_query = [instance['map_start_time']]
		self.scores_sorting = ScoreSortingPresets.get_preset(instance['mode_script'])
		self._set_results_view_mode('$<' + instance['map_name'] + '$> / ' + datetime.datetime.fromtimestamp(instance['map_start_time']).strftime("%c"))
		await self.refresh(player=player)


	async def _action_match_select(self, player, values, instance, **kwargs) -> None:
		if instance['map_start_time'] in self.scores_query:
			self.scores_query.remove(instance['map_start_time'])
		else:
			self.scores_query.append(instance['map_start_time'])
		await self.refresh(player=player)


	async def _button_back(self, player, values, **kwargs) -> None:
		self._set_match_view_mode()
		await self.refresh(player=player)


	async def _button_calculate_results(self, player, values, **kwargs) -> None:
		if self.scores_query:
			matches = await self.app.results.get_data_matches()
			mode_script = None
			for match in matches:
				if match.map_start_time in self.scores_query:
					mode_script = match.mode_script
					break

			self.scores_sorting = ScoreSortingPresets.get_preset(mode_script)
			self._set_results_view_mode('Selected Matches Results')
			await self.refresh(player=player)


	async def _button_clear_selection(self, player, values, **kwargs) -> None:
		if self.scores_query:
			self.scores_query = []
			await self.refresh(player=player)


	def get_score2_visible(self) -> bool:
		if self.scores_sorting == ScoreSortingPresets.TIMEATTACK:
			visible = False
		elif self.scores_sorting == ScoreSortingPresets.LAPS:
			visible = True
		elif self.scores_sorting == ScoreSortingPresets.ROUNDS:
			visible = False
		else:
			visible = False
		return visible


	def get_team_score_visible(self) -> bool:
		if self.scores_sorting == ScoreSortingPresets.TIMEATTACK:
			visible = False
		elif self.scores_sorting == ScoreSortingPresets.LAPS:
			visible = False
		elif self.scores_sorting == ScoreSortingPresets.ROUNDS:
			visible = False
		else:
			visible = True
		return visible


	def _set_match_view_mode(self) -> None:
		self.icon_substyle = 'Statistics'
		self.results_view_mode = False
		if self.persist_matches_page != 0:
			self.page = self.persist_matches_page
			self.persist_matches_page = 0
		self.title = 'Match History'


	def _set_results_view_mode(self, title: str) -> None:
		self.title = title
		self.icon_substyle = 'Rankings'
		self.results_view_mode = True
		self.persist_matches_page = self.page
		self.page = 1
