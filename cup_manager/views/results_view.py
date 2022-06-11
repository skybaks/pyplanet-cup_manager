import logging

from pyplanet.views.generics.list import ManualListView

from ..app_types import TeamPlayerScore, ScoreSortingPresets

logger = logging.getLogger(__name__)

class ResultsView(ManualListView):
	app = None

	title = 'Cup Results'
	icon_style = 'Icons128x128_1'
	icon_substyle = 'Rankings'

	get_data_method = None


	def __init__(self, app: any, player: any, score_query: 'list[int]', score_sorting: ScoreSortingPresets) -> None:
		super().__init__(self)
		self.app = app
		self.manager = app.context.ui
		self.player = player
		self.score_query = score_query
		self.score_sorting = score_sorting

		self.provide_search = False


	@classmethod
	def set_get_data_method(cls, method) -> None:
		cls.get_data_method = method


	async def get_fields(self):
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
				'width': 50,
				'type': 'label',
			},
			{
				'name': 'Count',
				'index': 'count',
				'sorting': False,
				'searching': False,
				'width': 20,
				'type': 'label',
			},
			{
				'name': 'Team',
				'index': 'team_score_str',
				'sorting': False,
				'searching': False,
				'width': 20,
				'type': 'label',
			},
			{
				'name': 'Score2',
				'index': 'player_score2_str',
				'sorting': False,
				'searching': False,
				'width': 20,
				'type': 'label',
			},
			{
				'name': 'Score1',
				'index': 'player_score_str',
				'sorting': False,
				'searching': False,
				'width': 20,
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
				'name': 'Country',
				'index': 'country',
				'sorting': False,
				'searching': False,
				'width': 30,
				'type': 'label',
			},
		]
		return fields


	async def get_data(self):
		items = []
		if self.get_data_method:
			scores = await self.get_data_method(self.score_query, self.score_sorting)	# type: list[TeamPlayerScore]
			index = 1
			for player_score in scores:
				items.append({
					'index': index,
					'login': player_score.login,
					'nickname': player_score.nickname,
					'country': player_score.country,
					'count': player_score.count,
					'team_score_str': player_score.team_score_str,
					'player_score2_str': player_score.player_score2_str,
					'player_score_str': player_score.player_score_str,
				})
				index += 1
		else:
			logger.error("Unexpected get_data_method is not set")
		return items
