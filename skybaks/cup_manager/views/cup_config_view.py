import logging
import re
from copy import deepcopy
from typing import Any

from .single_instance_view import SingleInstanceIndexActionsView, PagedData
from ..score_mode import SCORE_MODE

logger = logging.getLogger(__name__)


class ConfigContext:
    def __init__(self, data_name: str, view: "CupConfigView") -> None:
        self.name: str = data_name
        self.data: "dict[str, dict | list]" = view.config_data[data_name]
        self.view: "CupConfigView" = view
        self.value: "dict | list | None" = None
        self.selected_item: str = ""

    def get_selected_item(self) -> str:
        return self.selected_item

    def set_selected_item(self, item_name) -> None:
        if item_name in self.data:
            self.value = self.data[item_name]
            self.selected_item = item_name

    async def get_data(self) -> "dict[str]":
        return {
            "name": self.name,
            "id": self.selected_item,
            "value": self.value,
        }

    def get_action(self, action: str) -> str:
        action_name = action
        if action.startswith(self.view.id):
            action_name = action[len(self.view.id) + 2 :]
        return action_name


class ConfigContextNames(ConfigContext):
    help: "dict[str, str]" = {
        "id": """[Required]

The ID is the name which is used with the "//cup on" command to start the cup.""",
        "name": """[Required]

The Name is used as the display name for the cup in all ingame messages and interfaces.""",
        "preset_on": """[Optional]

Use preset_on and preset_off fields to link starting and stopping the cup to automatically trigger a settings preset. You can define one or the other or both.

- preset_on is equivalent to running "//cup setup <preset>" immediately after starting the cup

- preset_off is equivalent to running "//cup setup <preset>" imemdiately after the cup ends""",
        "preset_off": """[Optional]

Use preset_on and preset_off fields to link starting and stopping the cup to automatically trigger a settings preset. You can define one or the other or both.

- preset_on is equivalent to running "//cup setup <preset>" immediately after starting the cup

- preset_off is equivalent to running "//cup setup <preset>" imemdiately after the cup ends""",
        "map_count": """[Optional]

Use map_count to predefine the number of maps the cup will be played on. This is equivalent to running "//cup mapcount <map_count>" right after you start the cup.""",
        "payout": """[Optional]

Use payout to predefine the payout config this cup will be using. The value entered in this field should match the ID name of a payout defined in this config file. Predefining the payout here will make it easier to access from the results and will make it appear in the exported results.""",
        "scoremode": """[Optional]

Use scoremode to force the type of score behavior for the cup. This is equivalent to running "//cup scoremode <score_mode>" after starting a cup. If included the field should be set to one of the scoremode IDs found when running "//cup scoremode" """,
    }

    def __init__(self, view: "CupConfigView") -> None:
        super().__init__("names", view)
        self.editing: "dict[str, bool]" = dict()
        self.preset_data: PagedData = PagedData(max_per_page=6, name="preset")
        self.payout_data: PagedData = PagedData(max_per_page=6, name="payout")
        self.scoremode_data: PagedData = PagedData(max_per_page=6, name="scoremode")
        self.edit_selection: str = ""
        fields = [
            "id",
            "name",
            "map_count",
            "preset_on",
            "preset_off",
            "payout",
            "scoremode",
        ]
        for field in fields:
            self.editing.update({field: False})
            self.view.subscribe(f"names_{field}_edit", self.enable_edit)
            self.view.subscribe(f"names_{field}_edit_accept", self.accept_edit)
            self.view.subscribe(f"names_{field}_edit_cancel", self.cancel_edit)
            self.view.subscribe(f"names_{field}_delete", self.delete_field)
        self.view.subscribe("names_preset_on_page_next", self.preset_paging)
        self.view.subscribe("names_preset_on_page_prev", self.preset_paging)
        self.view.subscribe_index(
            "names_preset_on_selection_list", self.edit_preset_select
        )
        self.view.subscribe("names_preset_off_page_next", self.preset_paging)
        self.view.subscribe("names_preset_off_page_prev", self.preset_paging)
        self.view.subscribe_index(
            "names_preset_off_selection_list", self.edit_preset_select
        )
        self.view.subscribe("names_payout_page_next", self.payout_paging)
        self.view.subscribe("names_payout_page_prev", self.payout_paging)
        self.view.subscribe_index(
            "names_payout_selection_list", self.edit_payout_select
        )
        self.view.subscribe("names_scoremode_page_next", self.scoremode_paging)
        self.view.subscribe("names_scoremode_page_prev", self.scoremode_paging)
        self.view.subscribe_index(
            "names_scoremode_selection_list", self.edit_scoremode_select
        )

    async def update_paged_data(self) -> None:
        self.preset_data.data = list(
            self.view.config_data.get("presets", dict()).keys()
        )
        self.payout_data.data = list(
            self.view.config_data.get("payouts", dict()).keys()
        )
        self.scoremode_data.data = list(SCORE_MODE.keys())

    async def enable_edit(self, player, action: str, values: dict, **kwargs) -> None:
        match_result: "re.Match" = re.match("names_(\w+)_edit", self.get_action(action))
        if match_result and match_result.group(1) in self.editing:
            for key in self.editing.keys():
                self.editing[key] = True if key == match_result.group(1) else False
            self.edit_selection = self.value.get(match_result.group(1), "")
            await self.update_paged_data()
            await self.view.refresh(player=player)

    async def accept_edit(self, player, action: str, values: dict, **kwargs) -> None:
        match_result: "re.Match" = re.match(
            "names_(\w+)_edit_accept", self.get_action(action)
        )
        if match_result and match_result.group(1) in self.editing:
            edit_key = match_result.group(1)
            for key in self.editing.keys():
                self.editing[key] = False
            if edit_key == "id":
                old_name = self.get_selected_item()
                new_name = values.get("switched_entry")
                # Do we care about possibly overwriting an existing entry?
                self.data[new_name] = self.data[old_name]
                del self.data[old_name]
                self.view.selected_sidebar_item = new_name
            elif "switched_entry" in values:
                self.value[edit_key] = values.get("switched_entry")
            else:
                self.value[edit_key] = self.edit_selection
            await self.view.refresh(player=player)

    async def cancel_edit(self, player, action: str, values: dict, **kwargs) -> None:
        match_result: "re.Match" = re.match(
            "names_(\w+)_edit_cancel", self.get_action(action)
        )
        if match_result and match_result.group(1) in self.editing:
            for key in self.editing.keys():
                self.editing[key] = False
            await self.view.refresh(player=player)

    async def delete_field(self, player, action: str, values: dict, **kwargs) -> None:
        match_result: "re.Match" = re.match(
            "names_(\w+)_delete", self.get_action(action)
        )
        if match_result and match_result.group(1) in self.value:
            for key in self.editing.keys():
                self.editing[key] = False
            del self.value[match_result.group(1)]
            await self.view.refresh(player=player)

    async def edit_preset_select(self, player, action, values, index, **kwargs) -> None:
        new_selected_item = self.preset_data.get_current_page_data()[index]
        if new_selected_item != self.edit_selection:
            self.edit_selection = new_selected_item
            await self.view.refresh(player=player)

    async def edit_payout_select(self, player, action, values, index, **kwargs) -> None:
        new_selected_item = self.payout_data.get_current_page_data()[index]
        if new_selected_item != self.edit_selection:
            self.edit_selection = new_selected_item
            await self.view.refresh(player=player)

    async def edit_scoremode_select(
        self, player, action, values, index, **kwargs
    ) -> None:
        new_selected_item = self.scoremode_data.get_current_page_data()[index]
        if new_selected_item != self.edit_selection:
            self.edit_selection = new_selected_item
            await self.view.refresh(player=player)

    async def preset_paging(self, player, action, values, **kwargs) -> None:
        if "next" in action and self.preset_data.next_page():
            await self.view.refresh(player=player)
        elif "prev" in action and self.preset_data.prev_page():
            await self.view.refresh(player=player)

    async def payout_paging(self, player, action, values, **kwargs) -> None:
        if "next" in action and self.payout_data.next_page():
            await self.view.refresh(player=player)
        elif "prev" in action and self.payout_data.prev_page():
            await self.view.refresh(player=player)

    async def scoremode_paging(self, player, action, values, **kwargs) -> None:
        if "next" in action and self.scoremode_data.next_page():
            await self.view.refresh(player=player)
        elif "prev" in action and self.scoremode_data.prev_page():
            await self.view.refresh(player=player)

    async def get_data(self) -> "dict[str, Any]":
        context_data = await super().get_data()
        context_data.update(
            {"editing": self.editing, "help": self.help, "missing": dict()}
        )

        for field in self.editing:
            context_data["missing"][field] = field not in self.value

        context_data.update(self.preset_data.get_context_data(self.edit_selection))
        context_data.update(self.payout_data.get_context_data(self.edit_selection))
        context_data.update(self.scoremode_data.get_context_data(self.edit_selection))
        return context_data


class ConfigContextPresets(ConfigContext):
    def __init__(self, view: "CupConfigView") -> None:
        super().__init__("presets", view)


class ConfigContextPayouts(ConfigContext):
    def __init__(self, view: "CupConfigView") -> None:
        super().__init__("payouts", view)


class CupConfigView(SingleInstanceIndexActionsView):
    template_name = "cup_manager/config.xml"
    title = "Cup Configuration"
    icon_style = "Icons128x128_1"
    icon_substyle = "ProfileAdvanced"
    sidebar_data = PagedData(max_per_page=13, name="sidebar")

    def __init__(self, app, config: dict) -> None:
        super().__init__(app, "cup_manager.views.cup_config_view_displayed")
        self.config_data: "dict[str]" = deepcopy(config)
        self.config_tabs: "list[str]" = ["names", "presets", "payouts"]
        self.selected_tab_item: str = self.config_tabs[0]

        self.subscribe("sidebar_page_prev", self.sidebar_paging)
        self.subscribe("sidebar_page_next", self.sidebar_paging)
        self.subscribe_index("config_tab", self.select_config_tab)
        self.subscribe_index("config_sidebar", self.select_config_sidebar)

        self.config_context: "dict[str, ConfigContext]" = {
            "names": ConfigContextNames(self),
            "presets": ConfigContextPresets(self),
            "payouts": ConfigContextPayouts(self),
        }

    @property
    def selected_sidebar_item(self) -> str:
        return self.config_context[self.selected_tab_item].get_selected_item()

    @selected_sidebar_item.setter
    def selected_sidebar_item(self, value: str) -> None:
        self.config_context[self.selected_tab_item].set_selected_item(value)

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
        context.update(self.sidebar_data.get_context_data(self.selected_sidebar_item))
        context.update(
            {
                "config_context": await self.config_context[
                    self.selected_tab_item
                ].get_data()
            }
        )

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
