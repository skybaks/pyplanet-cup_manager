from datetime import datetime
import logging

from pyplanet.views.generics.list import ManualListView

from ..score_mode.mode_logic import get_sorting_from_mode

logger = logging.getLogger(__name__)


class MatchHistoryView(ManualListView):
    app = None
    title = "Match History"
    icon_style = "Icons128x128_1"
    icon_substyle = "Statistics"

    selected_map_times = {}  # type: dict[str, list[int]]

    def __init__(self, app, player) -> None:
        super().__init__(self)
        self.app = app
        self.manager = app.context.ui
        self.player = player
        self.provide_search = False
        if player.login not in self.selected_map_times:
            self.selected_map_times[player.login] = []

    async def get_fields(self) -> "list[dict[str, str | bool | int]]":
        fields = [
            {
                "name": "",
                "index": "selected",
                "sorting": False,
                "searching": False,
                "width": 6,
                "type": "label",
                "action": self._action_match_select,
            },
            {
                "name": "Map",
                "index": "map_name",
                "sorting": False,
                "searching": False,
                "width": 80,
                "type": "label",
                "action": self._action_view_match,
            },
            {
                "name": "Date",
                "index": "map_start_time_str",
                "sorting": False,
                "searching": False,
                "width": 40,
                "type": "label",
            },
            {
                "name": "Mode",
                "index": "mode_script",
                "sorting": False,
                "searching": False,
                "width": 50,
                "type": "label",
            },
        ]
        return fields

    async def get_buttons(self) -> "list[dict[str, str | bool | int]]":
        buttons = [
            {
                "title": "Sum Sel.",
                "width": 25,
                "action": self._button_calculate_results,
            },
            {
                "title": "Clear Sel.",
                "width": 25,
                "action": self._button_clear_selection,
            },
        ]
        return buttons

    async def get_data(self) -> "list[dict[str, str | bool | int]]":
        items = []
        maps = await self.app.results.get_data_matches()
        for map_data in maps:
            items.append(
                {
                    "selected": ""
                    if map_data.map_start_time
                    in self.selected_map_times[self.player.login]
                    else "",
                    "map_start_time_str": datetime.fromtimestamp(
                        map_data.map_start_time
                    ).strftime("%c"),
                    "map_start_time": map_data.map_start_time,
                    "mode_script": map_data.mode_script,
                    "map_name": map_data.map_name,
                    "map_uid": map_data.map_uid,
                    "mx_id": map_data.mx_id,
                }
            )
        return items

    async def _action_view_match(self, player, values, instance, **kwargs) -> None:
        scores_query = [instance["map_start_time"]]
        scores_sorting = get_sorting_from_mode(instance["mode_script"])
        await self.close(player=player)
        await self.app.results.open_view_match_results(
            player, scores_query, scores_sorting
        )

    async def _action_match_select(self, player, values, instance, **kwargs) -> None:
        if instance["map_start_time"] in self.selected_map_times[player.login]:
            self.selected_map_times[player.login].remove(instance["map_start_time"])
        else:
            self.selected_map_times[player.login].append(instance["map_start_time"])
        await self.refresh(player=player)

    async def _button_calculate_results(self, player, values, **kwargs) -> None:
        if self.selected_map_times[player.login]:
            self.selected_map_times[player.login].sort(reverse=True)
            matches = await self.app.results.get_data_specific_matches(
                self.selected_map_times[player.login]
            )
            mode_scripts = [match.mode_script for match in matches]
            scores_sorting = get_sorting_from_mode(mode_scripts)
            await self.close(player=player)
            await self.app.results.open_view_match_results(
                player, self.selected_map_times[player.login], scores_sorting
            )

    async def _button_clear_selection(self, player, values, **kwargs) -> None:
        if self.selected_map_times[player.login]:
            self.selected_map_times[player.login] = []
            await self.refresh(player=player)
