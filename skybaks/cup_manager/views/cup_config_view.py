import logging

from .single_instance_view import SingleInstanceView

logger = logging.getLogger(__name__)


class CupConfigView(SingleInstanceView):
    template_name = "cup_manager/config.xml"
    title = "Cup Configuration"
    icon_style = "Icons128x128_1"
    icon_substyle = "ProfileAdvanced"

    def __init__(self, app) -> None:
        super().__init__(app, "cup_manager.views.cup_config_view_displayed")
        self.config_tabs: "list[str]" = ["names", "presets", "payouts"]

    async def get_context_data(self):
        context = await super().get_context_data()
        context.update(
            {
                "title": self.title,
                "icon_style": self.icon_style,
                "icon_substyle": self.icon_substyle,
                "config_tabs": list()
            }
        )

        for tab in self.config_tabs:
            context["config_tabs"].append({
                "name": tab,
                "selected": False
            })
        return context
