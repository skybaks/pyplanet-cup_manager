import logging
import re
from copy import deepcopy

from .single_instance_view import SingleInstanceIndexActionsView, PagedData

logger = logging.getLogger(__name__)


class ConfigContextNames:
    help: "dict[str, str]" = {
        "id": "TODO: Help for ID",
        "name": "TODO: Help for Name",
        "preset_on": "TODO: Help for Preset On",
        "preset_off": "TODO: Help for Preset Off",
        "map_count": "TODO: Help for Map Count",
        "payout": "TODO: Help for Payout",
        "scoremode": "TODO: Help for ScoreMode",
    }

    def __init__(self, view: "CupConfigView") -> None:
        self.view = view
        self.editing: "dict[str, bool]" = {
            "id": False,
            "name": False,
            "map_count": False,
        }
        self.value: "dict[str, str]" = dict()
        self.view.subscribe("names_id_edit", self.enable_edit)
        self.view.subscribe("names_name_edit", self.enable_edit)
        self.view.subscribe("names_map_count_edit", self.enable_edit)
        # TODO: self.view.subscribe("names_id_delete", None)
        self.view.subscribe("names_id_edit_accept", self.accept_edit)
        self.view.subscribe("names_name_edit_accept", self.accept_edit)
        self.view.subscribe("names_map_count_edit_accept", self.accept_edit)
        self.view.subscribe("names_id_edit_cancel", self.cancel_edit)
        self.view.subscribe("names_name_edit_cancel", self.cancel_edit)
        self.view.subscribe("names_map_count_edit_cancel", self.cancel_edit)

    def get_selected_item(self) -> str:
        return self.value.get("id", "")

    def set_selected_item(self, item_name) -> None:
        if item_name in self.view.config_data["names"]:
            self.value: dict = self.view.config_data["names"][item_name]
            self.value.update({"id": item_name})

    def get_action(self, action: str) -> str:
        action_name = action
        if action.startswith(self.view.id):
            action_name = action[len(self.view.id) + 2 :]
        return action_name

    async def enable_edit(self, player, action: str, values: dict, **kwargs) -> None:
        match_result: "re.Match" = re.match("names_(\w+)_edit", self.get_action(action))
        if match_result and match_result.group(1) in self.editing:
            for key in self.editing.keys():
                self.editing[key] = True if key == match_result.group(1) else False
            await self.view.refresh(player=player)

    async def accept_edit(self, player, action: str, values: dict, **kwargs) -> None:
        match_result: "re.Match" = re.match(
            "names_(\w+)_edit_accept", self.get_action(action)
        )
        if match_result and match_result.group(1) in self.editing:
            for key in self.editing.keys():
                self.editing[key] = False
            if match_result.group(1) == "id":
                old_name = self.get_selected_item()
                new_name = values.get("switched_entry")
                # Do we care about possibly overwriting an existing entry?
                self.view.config_data["names"][new_name] = self.view.config_data[
                    "names"
                ][old_name]
                del self.view.config_data["names"][old_name]
                self.view.selected_sidebar_item = new_name
            elif match_result.group(1) in self.value:
                self.value[match_result.group(1)] = values.get("switched_entry")
            await self.view.refresh(player=player)

    async def cancel_edit(self, player, action: str, values: dict, **kwargs) -> None:
        match_result: "re.Match" = re.match(
            "names_(\w+)_edit_cancel", self.get_action(action)
        )
        if match_result and match_result.group(1) in self.editing:
            for key in self.editing.keys():
                self.editing[key] = False
            await self.view.refresh(player=player)

    async def get_data(self) -> "dict[str]":
        return {
            "editing": self.editing,
            "value": self.value,
            "help": self.help,
        }


class CupConfigView(SingleInstanceIndexActionsView):
    template_name = "cup_manager/config.xml"
    title = "Cup Configuration"
    icon_style = "Icons128x128_1"
    icon_substyle = "ProfileAdvanced"
    sidebar_data = PagedData(max_per_page=14)

    def __init__(self, app, config: dict) -> None:
        super().__init__(app, "cup_manager.views.cup_config_view_displayed")
        self.config_data: "dict[str]" = deepcopy(config)
        self.config_tabs: "list[str]" = list(self.config_data.keys())
        self.selected_tab_item: str = self.config_tabs[0]
        # self.selected_sidebar_item: str = ""

        self.subscribe("sidebar_page_prev", self.sidebar_paging)
        self.subscribe("sidebar_page_next", self.sidebar_paging)
        self.subscribe_index("config_tab", self.select_config_tab)
        self.subscribe_index("config_sidebar", self.select_config_sidebar)

        self.config_context = ConfigContextNames(self)

    @property
    def selected_sidebar_item(self) -> str:
        return self.config_context.get_selected_item()

    @selected_sidebar_item.setter
    def selected_sidebar_item(self, value: str) -> None:
        self.config_context.set_selected_item(value)

    async def get_context_data(self):
        context = await super().get_context_data()
        context.update(
            {
                "title": self.title,
                "icon_style": self.icon_style,
                "icon_substyle": self.icon_substyle,
                "config_tabs": list(),
            }
        )

        for tab in self.config_tabs:
            context["config_tabs"].append(
                {"name": tab, "selected": tab == self.selected_tab_item}
            )

        self.sidebar_data.data = await self.get_sidebar_items()
        sidebar_items = self.sidebar_data.get_current_page_data()
        context.update(
            {
                "sidebar_items": list(),
                "sidebar_page": self.sidebar_data.current_page,
                "sidebar_num_pages": self.sidebar_data.num_pages,
            }
        )
        for item in sidebar_items:
            context["sidebar_items"].append(
                {"name": item, "selected": item == self.selected_sidebar_item}
            )
        context.update({"config_context": await self.config_context.get_data()})

        return context

    async def get_sidebar_items(self) -> "list[str]":
        selected_config_data: "dict[str]" = self.config_data.get(self.selected_tab_item)
        selected_config_items: "list[str]" = list(selected_config_data.keys())
        # Default the sidebar item if not already set for this tab
        if (
            self.selected_sidebar_item not in selected_config_items
            and len(selected_config_items) > 0
        ):
            self.selected_sidebar_item = selected_config_items[0]
        return selected_config_items

    async def select_config_tab(
        self, player, action: str, values: dict, index: int, **kwargs
    ) -> None:
        new_selected_tab = self.config_tabs[index]
        if new_selected_tab != self.selected_tab_item:
            self.selected_tab_item = new_selected_tab
            await self.refresh(player=player)

    async def select_config_sidebar(
        self, player, action, values, index, **kwargs
    ) -> None:
        new_selected_item = self.sidebar_data.get_current_page_data()[index]
        if new_selected_item != self.selected_sidebar_item:
            self.selected_sidebar_item = new_selected_item
            await self.refresh(player=player)

    async def sidebar_paging(self, player, action, values, **kwargs) -> None:
        if "next" in action and self.sidebar_data.next_page():
            await self.refresh(player=player)
        elif "prev" in action and self.sidebar_data.prev_page():
            await self.refresh(player=player)
