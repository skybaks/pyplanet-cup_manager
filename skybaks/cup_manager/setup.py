import logging

from pyplanet.conf import settings
from pyplanet.contrib.command import Command
from pyplanet.apps.core.maniaplanet import callbacks as mp_signals
from pyplanet.apps.core.trackmania import callbacks as tm_signals


from .views import PresetsView

logger = logging.getLogger(__name__)


class SetupCupManager:
    def __init__(self, app) -> None:
        self.app = app
        self.instance = app.instance
        self.context = app.context

    async def on_start(self) -> None:
        self.context.signals.listen(
            mp_signals.map.map_start, self.check_points_repartition
        )
        self.context.signals.listen(
            mp_signals.flow.round_start, self.check_points_repartition
        )

        await self.instance.permission_manager.register(
            "setup_cup",
            "Change match settings from the cup_manager",
            app=self.app,
            min_level=2,
            namespace=self.app.namespace,
        )

        await self.instance.command_manager.register(
            Command(
                command="setup",
                aliases=["s"],
                namespace=self.app.namespace,
                target=self.command_setup,
                admin=True,
                perms="cup:setup_cup",
                description="Setup match settings based on some common presets.",
            ).add_param("preset", required=False),
        )

    async def command_setup(self, player, data, **kwargs) -> None:
        if not await self.instance.permission_manager.has_permission(
            player, "cup:setup_cup"
        ):
            return

        if data.preset:
            cmd_preset = data.preset.lower()
            presets = await self.app.config.get_cup_presets()
            selected_preset = None
            for preset_key, preset_data in presets.items():
                if cmd_preset == preset_key or cmd_preset in preset_data["aliases"]:
                    selected_preset = preset_key
                    break

            if selected_preset in presets:
                preset_data = presets[selected_preset]

                if (
                    "script" in preset_data
                    and self.instance.game.game in preset_data["script"]
                ):
                    await self.instance.mode_manager.set_next_script(
                        preset_data["script"][self.instance.game.game]
                    )

                if "settings" in preset_data:
                    # HACK: There is not a method to clear current script
                    # settings. I want to clear it our so that there is no
                    # overlap between presets
                    self.instance.mode_manager._next_settings_update = {}
                    await self.instance.mode_manager.update_next_settings(
                        preset_data["settings"]
                    )

                if "commands" in preset_data:
                    for command in preset_data["commands"]:
                        await self.instance.gbx.script(
                            *command, encode_json=False, response_id=False
                        )

                await self.app.instance.chat(
                    f"$ff0Set next script settings to preset: $<$fff{selected_preset}$>",
                    player,
                )
            else:
                await self.app.instance.chat(
                    f"$f00Unknown preset name $<$fff'{data.preset}'$>\nAvailable presets are: $<$fff{', '.join(presets.keys())}$>",
                    player,
                )
        else:
            view = PresetsView(self)
            await view.display(player=player)

    async def check_points_repartition(self, *args, **kwargs) -> None:
        # Need to verify points repartition in the mode script backend is set
        # to the values we wanted. This has been observed to be sometimes inconsistent.
        current_script = (await self.instance.mode_manager.get_current_script()).lower()
        if (
            "rounds" in current_script
            or "team" in current_script
            or "cup" in current_script
        ):
            script_current_settings = await self.instance.mode_manager.get_settings()

            if (
                "S_PointsRepartition" in script_current_settings
                and script_current_settings["S_PointsRepartition"]
            ):
                pointsrepartition_desired = [
                    int(point)
                    for point in script_current_settings["S_PointsRepartition"].split(
                        ","
                    )
                ]
                getpointsrepartition_response = await self.instance.gbx.script(
                    "Trackmania.GetPointsRepartition", encode_json=False
                )

                if "pointsrepartition" in getpointsrepartition_response:
                    pointsrepartition_actual = getpointsrepartition_response[
                        "pointsrepartition"
                    ]

                    if pointsrepartition_actual != pointsrepartition_desired:
                        logger.info(
                            "Current PointsRepartition is not equal to S_PointsRepartition. Performing correction..."
                        )
                        await self.instance.gbx.script(
                            *(
                                ["Trackmania.SetPointsRepartition"]
                                + [str(point) for point in pointsrepartition_desired]
                            ),
                            encode_json=False,
                            response_id=False,
                        )
