import logging
from datetime import datetime

from pyplanet.views.generics.list import ManualListView

from ..models import CupInfo, MatchInfo

logger = logging.getLogger(__name__)

class CupView(ManualListView):
	title = 'Cups'
	icon_style = 'Icons128x128_1'
	icon_substyle = 'Statistics'

	def __init__(self, app: any, player: any) -> None:
		super().__init__(self)
		self.app = app
		self.manager = app.context.ui
		self.player = player


	async def get_fields(self) -> 'list[dict[str, any]]':
		fields = [
			{
				'name': 'Cup Name',
				'index': 'cup_name',
				'sorting': True,
				'searching': True,
				'width': 70,
				'type': 'label',
				'action': self._action_select_cup,
			},
			{
				'name': 'Edition',
				'index': 'cup_edition',
				'sorting': True,
				'searching': True,
				'width': 60,
				'type': 'label',
			},
			{
				'name': 'Date',
				'index': 'cup_start_time_str',
				'sorting': True,
				'searching': True,
				'width': 40,
				'type': 'label',
			}
		]
		return fields


	async def get_data(self) -> 'list[dict[str, any]]':
		items = []
		cups_data = await self.app.active.get_data_cup_infos() # type: list[CupInfo]
		for cup_data in cups_data:
			items.append({
				# For display
				'cup_name': cup_data.cup_name,
				'cup_edition': f'Edition #{str(cup_data.cup_edition)}',
				'cup_start_time_str': datetime.fromtimestamp(cup_data.cup_start_time).strftime("%c"),
				# For row reference
				'cup_start_time': cup_data.cup_start_time,
			})
		return items


	async def _action_select_cup(self, player, values, instance, **kwargs) -> None:
		await self.close(player=player)
		await self.app.active.open_view_cup_maps(player, instance['cup_start_time'])


class CupMapsView(ManualListView):
	title = 'Cup Maps'
	icon_style = 'Icons128x128_1'
	icon_substyle = 'Statistics'

	def __init__(self, app: any, player: any, cup_start_time: int) -> None:
		super().__init__(self)
		self.app = app
		self.manager = app.context.ui
		self.player = player
		self.cup_start_time = cup_start_time


	async def get_fields(self) -> 'list[dict[str, any]]':
		fields = [
			{
				'name': 'Map',
				'index': 'map_name',
				'sorting': True,
				'searching': True,
				'width': 70,
				'type': 'label',
				'action': self._action_select_map,
			},
			{
				'name': 'Mode',
				'index': 'mode_script',
				'sorting': True,
				'searching': True,
				'width': 60,
				'type': 'label',
			},
			{
				'name': 'Date',
				'index': 'map_start_time_str',
				'sorting': True,
				'searching': True,
				'width': 40,
				'type': 'label',
			},
		]
		return fields


	async def get_buttons(self) -> 'list[dict[str, any]]':
		buttons = [
			{
				'title': '',	# back symbol (font awesome)
				'width': 7,
				'action': self._action_back,
			},
			{
				'title': 'Results',
				'width': 25,
				'action': self._action_total_results,
			}
		]
		return buttons


	async def get_data(self):
		items = []
		map_times = await self.app.active.get_data_cup_match_times(self.cup_start_time)	# type: list[int]
		match_infos = await self.app.results.get_data_specific_matches(map_times)	# type: list[MatchInfo]
		for match in match_infos:
			items.append({
				# Display
				'map_name': match.map_name,
				'mode_script': match.mode_script,
				'map_start_time_str': datetime.fromtimestamp(match.map_start_time).strftime("%c"),
				# Row reference
				'map_start_time': match.map_start_time,
			})
		return items


	async def _action_select_map(self, player, values, instance, **kwargs) -> None:
		await self.close(player=player)
		await self.app.active.open_view_results(player, [instance['map_start_time']], self.cup_start_time)


	async def _action_back(self, player, values, **kwargs) -> None:
		await self.close(player=player)
		await self.app.active.open_view_cups(player)


	async def _action_total_results(self, player, values, **kwargs) -> None:
		await self.close(player=player)
		map_times = await self.app.active.get_data_cup_match_times(self.cup_start_time)	# type: list[int]
		await self.app.active.open_view_results(player, map_times, self.cup_start_time)
