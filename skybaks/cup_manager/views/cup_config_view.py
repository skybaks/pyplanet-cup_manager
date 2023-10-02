import logging

from .single_instance_view import SingleInstanceIndexActionsView, PagedData

logger = logging.getLogger(__name__)


class CupConfigView(SingleInstanceIndexActionsView):
    template_name = "cup_manager/config.xml"
    title = "Cup Configuration"
    icon_style = "Icons128x128_1"
    icon_substyle = "ProfileAdvanced"
    sidebar_data = PagedData(max_per_page=14)

    def __init__(self, app) -> None:
        super().__init__(app, "cup_manager.views.cup_config_view_displayed")
        self.config_tabs: "list[str]" = ["names", "presets", "payouts"]
        self.selected_tab_item: str = self.config_tabs[0]
        self.selected_sidebar_item: str = ""

        self.subscribe("sidebar_page_prev", self.sidebar_paging)
        self.subscribe("sidebar_page_next", self.sidebar_paging)
        self.subscribe_index("config_tab", self.select_config_tab)
        self.subscribe_index("config_sidebar", self.select_config_sidebar)

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

        return context

    async def get_sidebar_items(self):
        return [
            "list_item_00",
            "list_item_01",
            "list_item_02",
            "list_item_03",
            "list_item_04",
            "list_item_05",
            "list_item_06",
            "list_item_07",
            "list_item_08",
            "list_item_09",
            "list_item_10",
            "list_item_11",
            "list_item_12",
            "added_item_1",
            "added_item_2",
            "added_item_3",
            "added_item_4",
            "added_item_5",
        ]

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
