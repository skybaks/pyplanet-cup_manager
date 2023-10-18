import logging
import re
from copy import deepcopy
from typing import Any

from pyplanet.views.generics import ask_confirmation

from .single_instance_view import SingleInstanceIndexActionsView, PagedData
from ..score_mode import SCORE_MODE

logger = logging.getLogger(__name__)

help_names_id: str = """[Required]

The ID is the name which is used with the "//cup on" command to start the cup."""
help_names_name: str = """[Required]

The Name is used as the display name for the cup in all ingame messages and interfaces."""
help_names_preset_on_off: str = """[Optional]

Use preset_on and preset_off fields to link starting and stopping the cup to automatically trigger a settings preset. You can define one or the other or both.

- preset_on is equivalent to running "//cup setup <preset>" immediately after starting the cup

- preset_off is equivalent to running "//cup setup <preset>" imemdiately after the cup ends"""
help_names_map_count: str = """[Optional]

Use map_count to predefine the number of maps the cup will be played on. This is equivalent to running "//cup mapcount <map_count>" right after you start the cup."""
help_names_payout: str = """[Optional]

Use payout to predefine the payout config this cup will be using. The value entered in this field should match the ID name of a payout defined in this config file. Predefining the payout here will make it easier to access from the results and will make it appear in the exported results."""
help_names_scoremode: str = """[Optional]

Use scoremode to force the type of score behavior for the cup. This is equivalent to running "//cup scoremode <score_mode>" after starting a cup. If included the field should be set to one of the scoremode IDs found when running "//cup scoremode" """
help_preset_id: str = """[Required]

The name which is used to identify the preset. This is the name which should be added to a \"names\" config for preset_on or preset_off and the name which should be used with the \"//cup setup <preset>\" command.
"""
help_preset_script: str = """[Required]

A script must be defined for at least one game. Multiple scripts can be defined to enable reuse of this preset across all the defined games.
"""
help_preset_settings: str = """[Required]

Enter script settings which will be applied with the preset.

The setting name goes in the first text field and the setting value goes in the second text field.
"""
help_payout_id: str = """[Required]

This unique ID is used to identify the payout."""
help_payout_vals: str = """[Required]

The values of planets that will be payed to players from the cup results. The first value will be given to the player in first, the second to the player in second, and so forth."""


def cast_setting(in_val: str) -> "bool | int | float | str":
    try:
        return int(in_val)
    except ValueError:
        pass

    try:
        return float(in_val)
    except ValueError:
        pass

    if in_val.lower() == "true":
        return True
    elif in_val.lower() == "false":
        return False

    return in_val


class ConfigContext:
    def __init__(self, data_name: str, view: "CupConfigView") -> None:
        self.name: str = data_name
        self.data: "dict[str, dict | list]" = view.config_data[data_name]
        self.view: "CupConfigView" = view
        self.value: "dict | list | None" = None
        self.help: "dict[str, str]" = dict()
        self.editing: "dict[str, bool]" = dict()
        self.selected_item: str = ""

    def get_selected_item(self) -> str:
        return self.selected_item

    def set_selected_item(self, item_name: str) -> None:
        if self.selected_item != item_name:
            self.update_editing(None)
        if item_name in self.data:
            self.value = self.data[item_name]
            self.selected_item = item_name

    def get_action(self, action: str) -> str:
        action_name = action
        if action.startswith(self.view.id):
            action_name = action[len(self.view.id) + 2 :]
        return action_name

    def update_editing(self, current) -> None:
        for key in self.editing.keys():
            self.editing[key] = True if key == current else False

    async def get_data(self) -> "dict[str]":
        return {
            "name": self.name,
            "id": self.selected_item,
            "value": self.value,
            "help": self.help,
            "editing": self.editing,
        }

    async def add_new_item(self) -> None:
        raise NotImplementedError

    async def delete_item(self) -> None:
        if self.selected_item in self.data:
            del self.data[self.selected_item]
            self.value = None
            self.selected_item = ""

    async def cancel_edit(
        self, player, action: str, values: dict, *args, **kwargs
    ) -> None:
        self.update_editing(None)
        await self.view.refresh(player=player)


class ConfigContextNames(ConfigContext):
    def __init__(self, view: "CupConfigView") -> None:
        super().__init__("names", view)
        self.help.update(
            {
                "id": help_names_id,
                "name": help_names_name,
                "preset_on": help_names_preset_on_off,
                "preset_off": help_names_preset_on_off,
                "map_count": help_names_map_count,
                "payout": help_names_payout,
                "scoremode": help_names_scoremode,
            }
        )
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
            self.update_editing(match_result.group(1))
            if self.value:
                self.edit_selection = self.value.get(match_result.group(1), "")
            await self.update_paged_data()
            await self.view.refresh(player=player)

    async def accept_edit(self, player, action: str, values: dict, **kwargs) -> None:
        match_result: "re.Match" = re.match(
            "names_(\w+)_edit_accept", self.get_action(action)
        )
        if match_result and match_result.group(1) in self.editing:
            edit_key = match_result.group(1)
            self.update_editing(None)
            if edit_key == "id":
                old_name = self.get_selected_item()
                new_name = values.get("switched_entry")
                if old_name != new_name:
                    # Do we care about possibly overwriting an existing entry?
                    self.data[new_name] = self.data[old_name]
                    del self.data[old_name]
                    self.view.selected_sidebar_item = new_name
            elif "switched_entry" in values:
                self.value[edit_key] = cast_setting(values.get("switched_entry"))
            else:
                self.value[edit_key] = self.edit_selection
            await self.view.refresh(player=player)

    async def delete_field(self, player, action: str, values: dict, **kwargs) -> None:
        match_result: "re.Match" = re.match(
            "names_(\w+)_delete", self.get_action(action)
        )
        if match_result and match_result.group(1) in self.value:
            self.update_editing(None)
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
        context_data.update({"missing": dict()})

        if self.value:
            for field in self.editing:
                context_data["missing"][field] = field not in self.value

        context_data.update(self.preset_data.get_context_data(self.edit_selection))
        context_data.update(self.payout_data.get_context_data(self.edit_selection))
        context_data.update(self.scoremode_data.get_context_data(self.edit_selection))
        return context_data

    async def add_new_item(self) -> None:
        new_name = "cup"
        counter = 1
        while "%s%i" % (new_name, counter) in self.data:
            counter += 1
            if counter > 10000:
                raise Exception(
                    "New cup name ID reached predefined auto-increment limit"
                )
        new_full_name = "%s%i" % (new_name, counter)
        self.data.update({new_full_name: {"name": "Cup Name"}})
        self.set_selected_item(new_full_name)


class ConfigContextPresets(ConfigContext):
    def __init__(self, view: "CupConfigView") -> None:
        super().__init__("presets", view)
        self.vals_data: PagedData = PagedData(6, "vals", append_empty=1)
        self.help.update(
            {
                "id": help_preset_id,
                "script": help_preset_script,
                "settings": help_preset_settings,
            }
        )
        self.editing.update({"vals": [False] * self.vals_data.max_per_page})
        fields = ["id", "script_tmnext", "script_tm", "script_sm"]
        for field in fields:
            self.editing.update({field: False})
            self.view.subscribe(f"preset_{field}_edit", self.enable_edit)
            self.view.subscribe(f"preset_{field}_edit_accept", self.accept_edit)
            self.view.subscribe(f"preset_{field}_edit_cancel", self.cancel_edit)
            self.view.subscribe(f"preset_{field}_delete", self.delete_field)
        self.view.subscribe("preset_settings_page_next", self.settings_paging)
        self.view.subscribe("preset_settings_page_prev", self.settings_paging)
        self.view.subscribe_index("preset_settings_edit", self.enable_edit_index)
        self.view.subscribe_index("preset_settings_edit_accept", self.accept_edit_index)
        self.view.subscribe_index("preset_settings_edit_cancel", self.cancel_edit)
        self.view.subscribe_index("preset_settings_delete", self.delete_index)

    def set_selected_item(self, item_name: str) -> None:
        super().set_selected_item(item_name)
        self.vals_data.data = self.value["settings"]

    def update_editing(self, current: "str | int") -> None:
        for key in self.editing.keys():
            if key != "vals":
                self.editing[key] = True if key == current else False
        for i in range(len(self.editing["vals"])):
            self.editing["vals"][i] = True if i == current else False

    async def enable_edit(self, player, action: str, values: dict, **kwargs) -> None:
        match_result: "re.Match" = re.match(
            "preset_(\w+)_edit", self.get_action(action)
        )
        if match_result and match_result.group(1) in self.editing:
            self.update_editing(match_result.group(1))
            await self.view.refresh(player=player)

    async def enable_edit_index(
        self, player, action: str, values: dict, index: int, **kwargs
    ) -> None:
        self.update_editing(index)
        await self.view.refresh(player=player)

    async def accept_edit(self, player, action: str, values: dict, **kwargs) -> None:
        match_result: "re.Match" = re.match(
            "preset_(\w+)_edit_accept", self.get_action(action)
        )
        if match_result and match_result.group(1) in self.editing:
            edit_key: str = match_result.group(1)
            self.update_editing(None)
            if edit_key == "id":
                old_name = self.get_selected_item()
                new_name = values.get("switched_entry")
                if old_name != new_name:
                    # Do we care about possibly overwriting an existing entry?
                    self.data[new_name] = self.data[old_name]
                    del self.data[old_name]
                    self.view.selected_sidebar_item = new_name
            elif "switched_entry" in values and edit_key.startswith("script"):
                game = edit_key.split("_")[-1]
                self.value["script"].update({game: values.get("switched_entry")})
            await self.view.refresh(player=player)

    async def accept_edit_index(
        self, player, action: str, values: dict, index: int, **kwargs
    ) -> None:
        self.update_editing(None)
        if "switched_entry" in values and "switched_entry2" in values:
            key = values["switched_entry"]
            if key:
                val = cast_setting(values["switched_entry2"])
                logger.debug(f"Saved setting {key}:{str(val)} as type {str(type(val))}")
                self.value["settings"][key] = val
        await self.view.refresh(player=player)

    async def delete_field(self, player, action: str, values: dict, **kwargs) -> None:
        match_result: "re.Match" = re.match(
            "preset_(\w+)_delete", self.get_action(action)
        )
        if match_result and match_result.group(1) in self.editing:
            delete_key: str = match_result.group(1)
            self.update_editing(None)
            if delete_key.startswith("script"):
                game = delete_key.split("_")[-1]
                if game in self.value["script"]:
                    del self.value["script"][game]
            await self.view.refresh(player=player)

    async def delete_index(
        self, player, action: str, values: dict, index: int, **kwargs
    ) -> None:
        self.update_editing(None)
        page_data = self.vals_data.get_current_page_data()
        if index < len(page_data):
            key = page_data[index][0]
            if key in self.value["settings"]:
                del self.value["settings"][key]
        await self.view.refresh(player=player)

    async def settings_paging(self, player, action, values, **kwargs) -> None:
        if "next" in action and self.vals_data.next_page():
            self.update_editing(None)
            await self.view.refresh(player=player)
        elif "prev" in action and self.vals_data.prev_page():
            self.update_editing(None)
            await self.view.refresh(player=player)

    async def get_data(self) -> "dict[str, Any]":
        context_data = await super().get_data()
        context_data.update(self.vals_data.get_context_data(selected_item=None))
        return context_data

    async def add_new_item(self) -> None:
        new_name = "preset"
        counter = 1
        while "%s%i" % (new_name, counter) in self.data:
            counter += 1
            if counter > 10000:
                raise Exception("New preset ID reached predefined auto-increment limit")
        new_full_name = "%s%i" % (new_name, counter)
        self.data.update(
            {new_full_name: {"aliases": list(), "script": dict(), "settings": dict()}}
        )
        self.set_selected_item(new_full_name)


class ConfigContextPayouts(ConfigContext):
    def __init__(self, view: "CupConfigView") -> None:
        super().__init__("payouts", view)
        self.vals_data: PagedData = PagedData(8, "vals", append_empty=1)
        self.help.update({"id": help_payout_id, "vals": help_payout_vals})
        self.editing.update(
            {"id": False, "vals": [False] * self.vals_data.max_per_page}
        )
        self.view.subscribe("payout_id_edit", self.enable_edit)
        self.view.subscribe("payout_id_edit_accept", self.accept_edit)
        self.view.subscribe("payout_id_edit_cancel", self.cancel_edit)
        self.view.subscribe("payout_vals_page_next", self.payout_paging)
        self.view.subscribe("payout_vals_page_prev", self.payout_paging)
        self.view.subscribe_index("payout_vals_edit", self.enable_edit_index)
        self.view.subscribe_index("payout_vals_edit_accept", self.accept_edit_index)
        self.view.subscribe_index("payout_vals_edit_cancel", self.cancel_edit)
        self.view.subscribe_index("payout_vals_delete", self.delete_index)

    def set_selected_item(self, item_name: str) -> None:
        super().set_selected_item(item_name)
        self.vals_data.data = self.value

    def update_editing(self, current: "str | int") -> None:
        for key in self.editing.keys():
            if key != "vals":
                self.editing[key] = True if key == current else False
        for i in range(len(self.editing["vals"])):
            self.editing["vals"][i] = True if i == current else False

    async def enable_edit(self, player, action: str, values: dict, **kwargs) -> None:
        match_result: "re.Match" = re.match(
            "payout_(\w+)_edit", self.get_action(action)
        )
        if match_result and match_result.group(1) in self.editing:
            self.update_editing(match_result.group(1))
            await self.view.refresh(player=player)

    async def enable_edit_index(
        self, player, action: str, values: dict, index: int, **kwargs
    ) -> None:
        self.update_editing(index)
        data_index = self.vals_data.page_index_to_data_index(index)
        if data_index >= len(self.value):
            self.value.append(0)
        await self.view.refresh(player=player)

    async def accept_edit(self, player, action: str, values: dict, **kwargs) -> None:
        match_result: "re.Match" = re.match(
            "payout_(\w+)_edit_accept", self.get_action(action)
        )
        if match_result and match_result.group(1) in self.editing:
            edit_key = match_result.group(1)
            self.update_editing(None)
            if edit_key == "id":
                old_name = self.get_selected_item()
                new_name = values.get("switched_entry")
                if old_name != new_name:
                    # Do we care about possibly overwriting an existing entry?
                    self.data[new_name] = self.data[old_name]
                    del self.data[old_name]
                    self.view.selected_sidebar_item = new_name
            await self.view.refresh(player=player)

    async def accept_edit_index(
        self, player, action: str, values: dict, index: int, **kwargs
    ) -> None:
        self.update_editing(None)
        data_index = self.vals_data.page_index_to_data_index(index)
        if data_index < len(self.value) and "switched_entry" in values:
            try:
                self.value[data_index] = int(values.get("switched_entry"))
            except ValueError as e:
                logger.error("Error setting value for payout field: " + str(e))
        await self.view.refresh(player=player)

    async def delete_index(
        self, player, action: str, values: dict, index: int, **kwargs
    ) -> None:
        self.update_editing(None)
        data_index = self.vals_data.page_index_to_data_index(index)
        if data_index < len(self.value):
            del self.value[data_index]
        await self.view.refresh(player=player)

    async def payout_paging(self, player, action, values, **kwargs) -> None:
        if "next" in action and self.vals_data.next_page():
            self.update_editing(None)
            await self.view.refresh(player=player)
        elif "prev" in action and self.vals_data.prev_page():
            self.update_editing(None)
            await self.view.refresh(player=player)

    async def get_data(self) -> "dict[str, Any]":
        context_data = await super().get_data()
        context_data.update(self.vals_data.get_context_data(selected_item=None))
        return context_data

    async def add_new_item(self) -> None:
        new_name = "payout"
        counter = 1
        while "%s%i" % (new_name, counter) in self.data:
            counter += 1
            if counter > 10000:
                raise Exception(
                    "New payout name ID reached predefined auto-increment limit"
                )
        new_full_name = "%s%i" % (new_name, counter)
        self.data.update({new_full_name: list()})
        self.set_selected_item(new_full_name)


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

        self.subscribe("config_button_close", self.close)
        self.subscribe("sidebar_page_prev", self.sidebar_paging)
        self.subscribe("sidebar_page_next", self.sidebar_paging)
        self.subscribe("sidebar_add_item", self.sidebar_add_item)
        self.subscribe("sidebar_del_item", self.sidebar_delete_item)
        self.subscribe("toolbar_validate", self.toolbar_validate)
        self.subscribe("toolbar_save", self.toolbar_save)
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

    async def sidebar_add_item(self, player, action, values, **kwargs) -> None:
        context: "ConfigContext" = self.config_context[self.selected_tab_item]
        await context.add_new_item()
        await self.refresh(player=player)

    async def sidebar_delete_item(self, player, action, values, **kwargs) -> None:
        context: "ConfigContext" = self.config_context[self.selected_tab_item]
        cancel = bool(
            await ask_confirmation(
                player=player,
                message=f'Deleting "{context.get_selected_item()}". Are you sure?',
                buttons=[{"name": "Delete"}, {"name": "Cancel"}],
                size="sm",
            )
        )
        if not cancel:
            await self.config_context[self.selected_tab_item].delete_item()
            await self.refresh(player=player)

    async def toolbar_validate(self, player, action, values, **kwargs) -> None:
        if await self.app.config.check_config_valid(self.config_data, player):
            await self.app.instance.chat("$ff0Config validation successful", player)

    async def toolbar_save(self, player, action, values, **kwargs) -> None:
        if await self.app.config.check_config_valid(self.config_data, player):
            filename = await self.app.config.save_config_file(self.config_data)
            if filename:
                await self.app.instance.chat(
                    f"$ff0Saved config to {str(filename)}", player
                )
