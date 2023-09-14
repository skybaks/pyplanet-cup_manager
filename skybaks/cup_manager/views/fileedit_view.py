import logging
import re

from pyplanet.apps.core.maniaplanet.models.player import Player

from .single_instance_view import SingleInstanceView

logger = logging.getLogger(__name__)


class FileEditView(SingleInstanceView):
    template_name = "cup_manager/fileedit.xml"
    title = "File Editor"
    icon_style = "Icons128x128_1"
    icon_substyle = "Editor"

    def __init__(self, app) -> None:
        super().__init__(app, "cup_manager.views.fileedit_displayed")
        self.subscribe("fileedit_button_close", self.close)
        self.subscribe("fileedit_button_save", self.save)
        self.subscribe("fileedit_button_reload", self.reload)
        self.file_text: str = ""
        self.selected_filename: str = ""

    async def handle_catch_all(
        self, player: Player, action: str, values: "dict[str]", **kwargs
    ):
        if action.startswith("fileedit_file_"):
            match = re.search("^fileedit_file_([0-9]+)$", action)
            if match and len(match.groups()) == 1:
                file_index = int(match.group(1))
                files = await self.get_files()
                if len(files) > file_index:
                    await self.select_file(files[file_index]["filename"], player)

    async def get_context_data(self) -> "dict[str]":
        context = await super().get_context_data()
        context.update(
            {
                "title": self.title,
                "icon_style": self.icon_style,
                "icon_substyle": self.icon_substyle,
            }
        )
        files = await self.get_files()
        context.update(files=files, file_text=self.file_text)
        return context

    async def get_files(self) -> "list[dict[str]]":
        filenames = await self.app.config.get_config_files()
        files = list()
        for file in filenames:
            files.append({"filename": file, "selected": self.selected_filename == file})
        return files

    async def select_file(self, filename: str, player: Player) -> None:
        logger.debug("Display selected file -> " + str(filename))
        self.selected_filename = filename
        self.file_text = await self.app.config.get_config_by_filename(filename)
        await self.refresh(player)

    async def save(
        self, player: Player, action: str, values: "dict[str]", *args, **kwargs
    ) -> None:
        pass

    async def reload(
        self, player: Player, action: str, values: "dict[str]", *args, **kwargs
    ) -> None:
        logger.debug("Reloading")
        if self.selected_filename:
            await self.select_file(self.selected_filename, player)
