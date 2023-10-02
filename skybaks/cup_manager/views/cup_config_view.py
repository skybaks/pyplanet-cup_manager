import logging

from .single_instance_view import SingleInstanceIndexActionsView

logger = logging.getLogger(__name__)


class CupConfigView(SingleInstanceIndexActionsView):
    template_name = "cup_manager/config.xml"
    title = "Cup Configuration"
    icon_style = "Icons128x128_1"
    icon_substyle = "ProfileAdvanced"

    def __init__(self, app) -> None:
        super().__init__(app, "cup_manager.views.cup_config_view_displayed")
        self.config_tabs: "list[str]" = ["names", "presets", "payouts"]

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
                "sidebar_items": list(),
            }
        )

        for tab in self.config_tabs:
            context["config_tabs"].append({"name": tab, "selected": False})

        sidebar_items = await self.get_sidebar_items()
        for item in sidebar_items:
            context["sidebar_items"].append({"name": item, "selected": False})

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
            "list_item_13",
        ]

    async def select_config_tab(
        self, player, action: str, values: dict, index: int, **kwargs
    ) -> None:
        logger.info(f"Clicked {str(self.config_tabs[index])}")

    async def select_config_sidebar(
        self, player, action, values, index, **kwargs
    ) -> None:
        logger.info(f"Clicked {str((await self.get_sidebar_items())[index])}")
