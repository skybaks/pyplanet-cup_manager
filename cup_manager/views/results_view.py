from inspect import iscoroutinefunction, isfunction
import logging

from pyplanet.views.generics.list import ManualListView

from ..app_types import ScoreSortingPresets, TeamPlayerScore

logger = logging.getLogger(__name__)

class ResultsView(ManualListView):
	title = 'Results'
	icon_style = 'Icons128x128_1'
	icon_substyle = 'Rankings'

	external_buttons = []

	def __init__(self, app: any, player: any, scores_query: 'list[int]', scores_sorting: ScoreSortingPresets):
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
		nickname_width = 105
		score2_width = 20
		team_width = 20
		if TeamPlayerScore.score2_relevant(self.scores_sorting):
			nickname_width -= score2_width
		if TeamPlayerScore.score_team_relevant(self.scores_sorting):
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

		if TeamPlayerScore.score2_relevant(self.scores_sorting):
			fields += [
				{
					'name': 'Team',
					'index': 'team_score_str',
					'sorting': False,
					'searching': False,
					'width': team_width,
					'type': 'label',
				}
			]

		fields += [
			{
				'name': 'Score',
				'index': 'player_score_str',
				'sorting': False,
				'searching': False,
				'width': 20,
				'type': 'label',
			},
		]

		if TeamPlayerScore.score_team_relevant(self.scores_sorting):
			fields += [
					{
						'name': 'Score2',
						'index': 'player_score2_str',
						'sorting': False,
						'searching': False,
						'width': score2_width,
						'type': 'label',
					}
			]

		fields += [
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
		buttons = []
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


class CupResultsView(ResultsView):
	def __init__(self, app: any, player: any, scores_query: 'list[int]', scores_sorting: ScoreSortingPresets, cup_start_time: int):
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
