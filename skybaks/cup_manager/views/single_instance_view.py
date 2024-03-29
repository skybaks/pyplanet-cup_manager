import re
import logging
import math
from asyncio import iscoroutinefunction
from typing import Callable

from pyplanet.views.template import TemplateView
from pyplanet.apps.core.maniaplanet.models.player import Player

logger = logging.getLogger(__name__)


def apply_pagination(frame: list, page: int, num_per_page: int) -> list:
    return frame[(page - 1) * num_per_page : page * num_per_page]


class PagedData:
    """Manages paged data for views
    Paging uses a 1-based index, i.e. The first page will be page 1.
    """

    def __init__(self, max_per_page: int, name: str, append_empty: int = 0) -> None:
        self.max_per_page: int = max_per_page
        self.current_page: int = 1
        self.name: str = name
        self.append_empty: int = append_empty
        self._data: "list | dict" = list()

    @property
    def data(self) -> list:
        items = self._data
        if isinstance(items, dict):
            items = [(key, val) for key, val in items.items()]
        if self.append_empty > 0:
            return items + ([None] * self.append_empty)
        else:
            return items

    @data.setter
    def data(self, value: "list | dict") -> None:
        self._data = value
        if self.current_page > self.num_pages:
            self.current_page = 1

    @property
    def num_pages(self) -> int:
        return int(math.ceil(len(self.data) / self.max_per_page))

    def page_index_to_data_index(self, index: int) -> int:
        return (self.current_page - 1) * self.max_per_page + index

    def get_current_page_data(self) -> list:
        return apply_pagination(self.data, self.current_page, self.max_per_page)

    def next_page(self, *args, **kwargs) -> bool:
        old_page = self.current_page
        self.current_page = min(self.current_page + 1, self.num_pages)
        return self.current_page != old_page

    def prev_page(self, *args, **kwargs) -> bool:
        old_page = self.current_page
        self.current_page = max(self.current_page - 1, 1)
        return self.current_page != old_page

    def get_context_data(
        self, selected_item: str
    ) -> "dict[str, list[dict[str, str | bool]] | int]":
        context_data = {
            f"{self.name}_items": list(),
            f"{self.name}_page": self.current_page,
            f"{self.name}_num_pages": self.num_pages,
            f"{self.name}_max_per_page": self.max_per_page,
        }
        for item in self.get_current_page_data():
            context_data[f"{self.name}_items"].append(
                {"name": item, "selected": item == selected_item}
            )
        return context_data


class SingleInstanceView(TemplateView):
    def __init__(self, app, tag) -> None:
        super().__init__(self)
        self.app = app
        self.manager = app.context.ui
        self.tag = tag

    async def refresh(self, player, *args, **kwargs):
        await self.display(player=player)

    async def display(self, player=None):
        login = player.login if isinstance(player, Player) else player
        if not player:
            raise Exception("No player/login given to display to")
        player = (
            player
            if isinstance(player, Player)
            else await self.app.instance.player_manager.get_player(
                login=login, lock=False
            )
        )

        other_view = player.attributes.get(self.tag, None)
        if other_view and isinstance(other_view, str):
            other_manialink = self.app.instance.ui_manager.get_manialink_by_id(
                other_view
            )
            if isinstance(other_manialink, SingleInstanceView):
                await other_manialink.close(player)
        player.attributes.set(self.tag, self.id)

        return await super().display(player_logins=[login])

    async def close(self, player, *args, **kwargs):
        if self.player_data and player.login in self.player_data:
            del self.player_data[player.login]
        await self.hide(player_logins=[player.login])
        player.attributes.set(self.tag, None)


class SingleInstanceIndexActionsView(SingleInstanceView):
    def __init__(self, app, tag) -> None:
        super().__init__(app, tag)
        self.receivers_index: "dict[str, list[Callable]]" = dict()

    def subscribe_index(self, action: str, target: Callable):
        if action not in self.receivers_index:
            self.receivers_index[action] = list()
        self.receivers_index[action].append(target)

    async def handle_catch_all(self, player, action: str, values, **kwargs):
        match_result: "re.Match[str]" = re.match("(.*)_([0-9]+)", action)
        if (
            match_result
            and len(match_result.groups()) == 2
            and match_result.group(1) in self.receivers_index
        ):
            try:
                index: int = int(match_result.group(2))
                action_methods: "list[Callable]" = self.receivers_index.get(
                    match_result.group(1)
                )
                for action_method in action_methods:
                    if iscoroutinefunction(action_method):
                        await action_method(player, action, values, index)
                    else:
                        action_method(player, action, values, index)
            except ValueError as e:
                logger.error(
                    f'Got invalid value "{str(match_result.group(2))}" from handle_catch_all for action "{str(action)}"'
                )
        else:
            await super().handle_catch_all(player, action, values, **kwargs)
