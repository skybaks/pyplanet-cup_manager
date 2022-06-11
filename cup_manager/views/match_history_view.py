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

	def __init__(self, app, player) -> None:
		super().__init__(self)
		self.app = app
		self.manager = app.context.ui
		self.player = player
		self.provide_search = False
		self.results_view_show_score2 = False
		self.scores_query = []
		self.scores_mode_script = ''
		self._results_view_mode = False
		self._persist_matches_page = 0
		self._selected_matches = []
		self.team_score_mode = False


	async def get_fields(self) -> list:
		fields = []
		if self._results_view_mode:
			nickname_width = 105
			score2_width = 20
			team_width = 20

			if self.results_view_show_score2:
				nickname_width -= score2_width
			if self.team_score_mode:
				nickname_width -= team_width

			fields.append(
				{
					'name': '#',
					'index': 'index',
					'sorting': False,
					'searching': False,
					'width': 10,
					'type': 'label',
				},
			)
			fields.append(
				{
					'name': 'Nickname',
					'index': 'nickname',
					'sorting': False,
					'searching': False,
					'width': nickname_width,
					'type': 'label',
				},
			)
			fields.append(
				{
					'name': 'Login',
					'index': 'login',
					'sorting': False,
					'searching': False,
					'width': 50,
					'type': 'label',
				},
			)
			if self.team_score_mode:
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
			if self.results_view_show_score2:
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
			scores = await self.app.get_data_scores(self.scores_query, ScoreSortingPresets.get_preset(self.scores_mode_script))
			index = 1
			for player_score in scores:
				items.append({
					'index': index,
					'login': player_score.login,
					'nickname': player_score.nickname,
					'country': player_score.country,
					#'score': player_score.player_score,
					'player_score_str': player_score.player_score_str,
					#'score2': player_score.player_score2,
					'player_score2_str': player_score.player_score2_str,
					'team_score_str':player_score.team_score_str,
				})
				index += 1

		if not items:
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
		self.scores_query = instance['map_start_time']
		self.scores_mode_script = instance['mode_script']
		self._set_results_view_mode(
			'$<' + instance['map_name'] + '$> / ' + datetime.datetime.fromtimestamp(instance['map_start_time']).strftime("%c"),
			show_score2='laps' in instance['mode_script'].lower(),
			show_team_score=len(await self.app.get_data_team_scores(instance['map_start_time'])) > 0
		)
		await self.refresh(player=player)


	async def _action_match_select(self, player, values, instance, **kwargs):
		if instance['map_start_time'] in self._selected_matches:
			self._selected_matches.remove(instance['map_start_time'])
		else:
			self._selected_matches.append(instance['map_start_time'])
		await self.refresh(player=player)


	async def _button_back(self, player, values, **kwargs):
		self._set_match_view_mode()
		await self.refresh(player=player)


	async def _button_calculate_results(self, player, values, **kwargs):
		if self._selected_matches:
			matches = await self.app.get_data_matches()
			mode_script = None
			for match in matches:
				if match.map_start_time in self._selected_matches:
					mode_script = match.mode_script
					break

			show_team_score = False
			for selected_match in self._selected_matches:
				if len(await self.app.get_data_team_scores(selected_match)) > 0:
					show_team_score = True
					break

			self.scores_query = self._selected_matches
			self.scores_mode_script = mode_script
			self._set_results_view_mode(
				'Selected Matches Results',
				show_score2='laps' in mode_script.lower(),
				show_team_score=show_team_score
			)
			await self.refresh(player=player)


	async def _button_clear_selection(self, player, values, **kwargs):
		if self._selected_matches:
			self._selected_matches = []
			await self.refresh(player=player)


	def _set_match_view_mode(self):
		self.icon_substyle = 'Statistics'
		self._results_view_mode = False
		if self._persist_matches_page != 0:
			self.page = self._persist_matches_page
			self._persist_matches_page = 0
		self.title = 'Match History'


	def _set_results_view_mode(self, title: str, show_score2: bool=False, show_team_score: bool=False):
		self.title = title
		self.icon_substyle = 'Rankings'
		self.results_view_show_score2 = show_score2
		self.team_score_mode = show_team_score
		self._results_view_mode = True
		self._persist_matches_page = self.page
		self.page = 1
