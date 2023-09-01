import logging
from datetime import datetime

from pyplanet.views.generics.list import ManualListView

from ..models import CupInfo, MatchInfo

logger = logging.getLogger(__name__)


class CupView(ManualListView):
    title = "Cups"
    icon_style = "Icons128x128_1"
    icon_substyle = "Statistics"

    def __init__(self, app: any, player: any) -> None:
        super().__init__(self)
        self.app = app
        self.manager = app.context.ui
        self.player = player

    async def get_fields(self) -> "list[dict[str, any]]":
        fields = [
            {
                "name": "Cup Name",
                "index": "cup_name",
                "sorting": True,
                "searching": True,
                "width": 50,
                "type": "label",
                "action": self._action_select_cup,
            },
            {
                "name": "Edition",
                "index": "cup_edition",
                "sorting": True,
                "searching": True,
                "width": 30,
                "type": "label",
            },
            {
                "name": "Host",
                "index": "host_str",
                "sorting": True,
                "searching": True,
                "width": 40,
                "type": "label",
            },
            {
                "name": "Date",
                "index": "cup_start_time_str",
                "sorting": True,
                "searching": True,
                "width": 50,
                "type": "label",
            },
            {
                "name": "Map(s)",
                "index": "maps_str",
                "sorting": True,
                "searching": True,
                "width": 20,
                "type": "label",
            },
        ]
        return fields

    async def get_data(self) -> "list[dict[str, any]]":
        items = []
        cups_data = await self.app.active.get_data_cup_info()  # type: list[CupInfo]
        for cup_data in cups_data:
            map_start_times = await self.app.active.get_data_cup_match_times(
                cup_data.cup_start_time
            )  # type: list[int]
            items.append(
                {
                    # For display
                    "cup_name": cup_data.cup_name,
                    "cup_edition": f"Edition #{str(cup_data.cup_edition)}",
                    "cup_start_time_str": datetime.fromtimestamp(
                        cup_data.cup_start_time
                    ).strftime("%c"),
                    "maps_str": str(len(map_start_times)),
                    "host_str": str(
                        cup_data.cup_host_nickname if cup_data.cup_host_nickname else ""
                    ),
                    # For row reference
                    "cup_start_time": cup_data.cup_start_time,
                }
            )
        return items

    async def _action_select_cup(self, player, values, instance, **kwargs) -> None:
        await self.close(player=player)
        await self.app.active.open_view_cup_maps(player, instance["cup_start_time"])


class CupMapsView(ManualListView):
    title = "Cup Maps"
    icon_style = "Icons128x128_1"
    icon_substyle = "Statistics"

    def __init__(self, app: any, player: any, cup_start_time: int) -> None:
        super().__init__(self)
        self.app = app
        self.manager = app.context.ui
        self.player = player
        self.cup_start_time = cup_start_time

    async def get_fields(self) -> "list[dict[str, any]]":
        fields = [
            {
                "name": "Map",
                "index": "map_name",
                "sorting": True,
                "searching": True,
                "width": 70,
                "type": "label",
                "action": self._action_select_map,
            },
            {
                "name": "Mode",
                "index": "mode_script",
                "sorting": True,
                "searching": True,
                "width": 60,
                "type": "label",
            },
            {
                "name": "Date",
                "index": "map_start_time_str",
                "sorting": True,
                "searching": True,
                "width": 40,
                "type": "label",
            },
        ]
        return fields

    async def get_buttons(self) -> "list[dict[str, any]]":
        buttons = [
            {
                "title": "",  # back symbol (font awesome)
                "width": 7,
                "action": self._action_back,
            },
            {
                "title": "Results",
                "width": 25,
                "action": self._action_total_results,
            },
        ]
        return buttons

    async def get_data(self):
        items = []
        map_times = await self.app.active.get_data_cup_match_times(
            self.cup_start_time
        )  # type: list[int]
        match_infos = await self.app.results.get_data_specific_matches(
            map_times
        )  # type: list[MatchInfo]
        for match in match_infos:
            items.append(
                {
                    # Display
                    "map_name": match.map_name,
                    "mode_script": match.mode_script,
                    "map_start_time_str": datetime.fromtimestamp(
                        match.map_start_time
                    ).strftime("%c"),
                    # Row reference
                    "map_start_time": match.map_start_time,
                }
            )
        return items

    async def _action_select_map(self, player, values, instance, **kwargs) -> None:
        await self.close(player=player)
        await self.app.active.open_view_results(
            player, [instance["map_start_time"]], self.cup_start_time
        )

    async def _action_back(self, player, values, **kwargs) -> None:
        await self.close(player=player)
        await self.app.active.open_view_cups(player)

    async def _action_total_results(self, player, values, **kwargs) -> None:
        await self.close(player=player)
        map_times = await self.app.active.get_data_cup_match_times(
            self.cup_start_time
        )  # type: list[int]
        await self.app.active.open_view_results(player, map_times, self.cup_start_time)


class AddRemoveCupMatchesView(ManualListView):
    app = None

    title = "Add/Remove Cup Matches"
    icon_style = "Icons128x128_1"
    icon_substyle = "Statistics"

    get_data_method = None

    def __init__(self, app: any, player: any) -> None:
        super().__init__(self)
        self.app = app
        self.manager = app.context.ui
        self.player = player

    @classmethod
    def set_get_data_method(cls, method) -> None:
        cls.get_data_method = method

    async def get_fields(self):
        fields = [
            {
                "name": "Add/Remove Map",
                "index": "selected_str",
                "sorting": False,
                "searching": False,
                "width": 35,
                "type": "label",
                "action": self._action_match_select,
            },
            {
                "name": "Date",
                "index": "match_time_str",
                "sorting": False,
                "searching": False,
                "width": 40,
                "type": "label",
            },
            {
                "name": "Map Name",
                "index": "map_name_str",
                "sorting": False,
                "searching": False,
                "width": 50,
                "type": "label",
            },
            {
                "name": "Mode Script",
                "index": "mode_script",
                "sorting": False,
                "searching": False,
                "width": 50,
                "type": "label",
            },
        ]
        return fields

    async def get_data(self) -> list:
        sel_str_true = "$f55 Remove from Cup"
        sel_str_false = "$0cf Add to Cup"

        items = []
        if self.get_data_method:
            matches = await self.get_data_method()  # type: list[MatchInfo]
            selected_matches = list(
                await self.app.get_selected_matches()
            )  # type: list[int]
            for match_info in matches:
                items.append(
                    {
                        "selected": match_info.map_start_time in selected_matches,
                        "map_start_time": match_info.map_start_time,
                        "selected_str": sel_str_true
                        if match_info.map_start_time in selected_matches
                        else sel_str_false,
                        "match_time_str": datetime.fromtimestamp(
                            match_info.map_start_time
                        ).strftime("%c"),
                        "map_name_str": match_info.map_name,
                        "mode_script": match_info.mode_script,
                    }
                )
                if match_info.map_start_time in selected_matches:
                    selected_matches.remove(match_info.map_start_time)
            for match_start_time in selected_matches:
                items.insert(
                    0,
                    {
                        "selected": True,
                        "map_start_time": match_start_time,
                        "selected_str": sel_str_true,
                        "match_time_str": datetime.fromtimestamp(
                            match_start_time
                        ).strftime("%c"),
                        "map_name_str": "No score data for this map yet",
                        "mode_script": "Unkown",
                    },
                )
        return items

    async def _action_match_select(self, player, values, instance, **kwargs):
        if instance["selected"]:
            await self.app.remove_selected_match(instance["map_start_time"])
        else:
            await self.app.add_selected_match(instance["map_start_time"])
        await self.refresh(player=player)
