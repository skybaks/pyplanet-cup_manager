from pyplanet.views.template import TemplateView
from pyplanet.apps.core.maniaplanet.models.player import Player


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
