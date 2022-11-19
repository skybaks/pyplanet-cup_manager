from inspect import iscoroutinefunction, isfunction
import logging

from pyplanet.views.generics.list import ManualListView

from ..app_types import TeamPlayerScore
from ..score_mode import ScoreModeBase

logger = logging.getLogger(__name__)


class ResultsView(ManualListView):
	title = 'Results'
	icon_style = 'Icons128x128_1'
	icon_substyle = 'Rankings'

	external_buttons = []

	def __init__(self, app: any, player: any, scores_query: 'list[int]', scores_sorting: ScoreModeBase):
		super().__init__(self)
		self.app = app
		self.manager = app.context.ui
		self.player = player
		self.scores_query = scores_query
		self.scores_sorting = scores_sorting


	@classmethod
	def add_button(cls, name, target, visible) -> None:
		cls.external_buttons.append({
			'title': name,
			'action': target,
			'width': 25,
			'visible': visible,
		})


	async def get_fields(self) -> 'list[dict[str, any]]':
		fields = []
		nickname_width = 100
		score_width = 25
		if self.scores_sorting.score2_relevant():
			nickname_width -= score_width
		if self.scores_sorting.scoreteam_relevant():
			nickname_width -= score_width

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
		]

		score_names = self.scores_sorting.get_score_names()

		if self.scores_sorting.scoreteam_relevant():
			fields += [
				{
					'name': score_names.scoreteam_name,
					'index': 'team_score_str',
					'sorting': False,
					'searching': False,
					'width': score_width,
					'type': 'label',
				}
			]

		fields += [
			{
				'name': score_names.score1_name,
				'index': 'player_score_str',
				'sorting': False,
				'searching': False,
				'width': 25,
				'type': 'label',
			},
		]

		if self.scores_sorting.score2_relevant():
			fields += [
					{
						'name': score_names.score2_name,
						'index': 'player_score2_str',
						'sorting': False,
						'searching': False,
						'width': score_width,
						'type': 'label',
					}
			]

		fields += [
			{
				'name': 'Login',
				'index': 'login',
				'sorting': False,
				'searching': False,
				'width': 40,
				'type': 'label',
			},
			{
				'name': 'Country',
				'index': 'country',
				'sorting': False,
				'searching': False,
				'width': 30,
				'type': 'label',
			},
		]
		return fields


	async def get_buttons(self) -> 'list[dict[str, any]]':
		buttons = [
			{
				'title': '',	# sort symbol (font awesome)
				'width': 7,
				'action': self._action_resort,
			},
		]
		for extern_button in self.external_buttons:
			if (iscoroutinefunction(extern_button['visible']) and await extern_button['visible'](player=self.player, view=self)) \
					or (isfunction(extern_button['visible']) and extern_button['visible'](player=self.player, view=self)) \
					or (extern_button['visible']):
				buttons.append(extern_button)
		return buttons


	async def get_data(self) -> 'list[dict[str, any]]':
		items = []
		scores = await self.app.results.get_data_scores(self.scores_query, self.scores_sorting)	# type: list[TeamPlayerScore]
		for player_score in scores:
			highlight = '$0cf' if player_score.login == self.player.login else ''
			items.append({
				'index': highlight + str(player_score.placement),
				'login': highlight + str(player_score.login),
				'nickname': highlight + str(player_score.nickname),
				'country': highlight + str(player_score.country),
				'player_score_str': highlight + str(player_score.player_score_str),
				'player_score2_str': highlight + str(player_score.player_score2_str),
				'team_score_str': highlight + str(player_score.team_score_str),
			})
		return items
	

	async def _action_resort(self, player, values, **kwargs) -> None:
		await self.app.results.open_view_scoremode(player, self)


class CupResultsView(ResultsView):
	def __init__(self, app: any, player: any, scores_query: 'list[int]', scores_sorting: ScoreModeBase, cup_start_time: int):
		super().__init__(app, player, scores_query, scores_sorting)
		self.cup_start_time = cup_start_time


	async def get_buttons(self) -> 'list[dict[str, any]]':
		buttons = await super().get_buttons()
		buttons.insert(0, {
			'title': '',	# back symbol (font awesome)
			'width': 7,
			'action': self._action_back,
		})
		return buttons


	async def _action_back(self, player, values, **kwargs) -> None:
		await self.close(player=player)
		await self.app.active.open_view_cup_maps(player, self.cup_start_time)



class GeneralResultsView(ResultsView):
	async def get_buttons(self) -> 'list[dict[str, any]]':
		buttons = await super().get_buttons()
		buttons.insert(0, {
			'title': '',	# back symbol (font awesome)
			'width': 7,
			'action': self._action_back,
		})
		return buttons


	async def _action_back(self, player, values, **kwargs) -> None:
		await self.close(player=player)
		await self.app.results.open_view_match_history(player)
