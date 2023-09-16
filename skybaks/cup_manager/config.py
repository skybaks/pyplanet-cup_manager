import logging
import os
import json

from pyplanet.conf import settings
from pyplanet.core.instance import Instance
from pyplanet.contrib.command import Command


logger = logging.getLogger(__name__)

FALLBACK_CONFIG: "dict[str]" = dict()


class CupConfiguration:
    def __init__(self, app) -> None:
        self.app = app
        self.instance: Instance = app.instance
        self.config_path = "UserData/Maps/MatchSettings"
        self.config: "dict[str]" = dict()
        try:
            self.config_path = settings.CUP_MANAGER_CONFIG_PATH
        except KeyError:
            logger.debug("CUP_MANAGER_CONFIG_PATH not defined in local.py")

    async def on_start(self) -> None:
        await self.instance.command_manager.register(
            Command(
                command="config",
                aliases=["c"],
                namespace=self.app.namespace,
                target=self.command_config,
                admin=True,
                perms="cup:manage_cup",
                description="Load in a new configuration for the cup manager plugin",
            ).add_param(
                "command",
                nargs=1,
                type=str,
                required=False,
                help="load, download",
            )
        )

        await self.load_config()

    async def get_cup_presets(self) -> "dict[str, dict]":
        return self.config.get("presets")

    async def get_cup_payouts(self) -> "dict[str, dict]":
        return self.config.get("payouts")

    async def get_cup_names(self) -> "dict[str, dict]":
        return self.config.get("names")

    async def command_config(self, player, data, *args, **kwargs) -> None:
        if not data.cmd:
            # TODO: Implement config editor views
            pass
        elif data.cmd == "load":
            load_filename = kwargs.get("load", "")
        elif data.cmd == "download":
            download_link = kwargs.get("download", "")

    async def load_config_from_file(self, filename, player=None) -> dict:
        loaded_config = await self.load_json_from_config_dir(filename)
        # TODO: Perform validation
        if loaded_config:
            if player:
                await self.instance.chat(
                    f"$ff0Loaded cup configuration from {filename}", player.login
                )
            logger.debug(f"Loaded cup configuration from {filename}")
            return loaded_config
        return dict()

    async def load_config_from_settings(self, player=None) -> dict:
        settings_config_presets = await self.get_setting_safe("CUP_MANAGER_PRESETS")
        settings_config_payouts = await self.get_setting_safe("CUP_MANAGER_PAYOUTS")
        settings_config_names = await self.get_setting_safe("CUP_MANAGER_NAMES")
        if settings_config_presets or settings_config_payouts or settings_config_names:
            loaded_config = {
                "presets": settings_config_presets,
                "payouts": settings_config_payouts,
                "names": settings_config_names,
            }
            if player:
                await self.instance.chat(
                    f"$ff0Loaded cup configuration from pyplanet settings", player.login
                )
            logger.debug("Loaded cup configuration from pyplanet settings")
            return loaded_config
        return dict()

    async def load_config(self) -> None:
        loaded_config_file = await self.load_config_from_file("cup_manager_config.json")
        if loaded_config_file:
            self.config = loaded_config_file
            return

        loaded_config_file = await self.load_config_from_settings()
        if loaded_config_file:
            self.config = loaded_config_file
            return

        self.config = get_fallback_config()
        logger.debug("Using fallback config")

    async def get_setting_safe(self, name):
        try:
            return settings.__getattr__(name)
        except KeyError:
            logger.debug("%s not defined in local.py" % name)

    async def read_file_from_config_dir(self, filename: str) -> str:
        file_path = os.path.join(self.config_path, filename)
        try:
            if await self.instance.storage.driver.exists(file_path):
                async with self.instance.storage.driver.open(file_path, "r") as r_file:
                    return await r_file.read()
        except Exception as e:
            logger.exception(e)
        return ""

    async def write_file_from_config_dir(self, filename: str, contents: str) -> None:
        file_path = os.path.join(self.config_path, filename)
        try:
            async with self.instance.storage.driver.open(file_path, "w") as w_file:
                await w_file.write(contents)
        except Exception as e:
            logger.exception(e)

    async def load_json_from_config_dir(self, filename: str) -> dict:
        file_contents = await self.read_file_from_config_dir(filename)
        if file_contents:
            try:
                return json.loads(file_contents)
            except:
                logger.error("Error decoding json file " + filename)
        return dict()


def get_fallback_config() -> "dict[str]":
    global FALLBACK_CONFIG
    if not FALLBACK_CONFIG:
        logger.debug("Initializing fallback config")
        FALLBACK_CONFIG = {
            "presets": {
                "rounds180": {
                    "aliases": ["smurfscup", "sc"],
                    "script": {
                        "tm": "Rounds.Script.txt",
                        "tmnext": "Trackmania/TM_Rounds_Online.Script.txt",
                    },
                    "settings": {
                        "S_FinishTimeout": 10,
                        "S_PointsLimit": 180,
                        "S_WarmUpNb": 1,
                        "S_WarmUpDuration": 0,
                        "S_PointsRepartition": "50,45,41,38,36,34,32,30,28,26,24,22,20,18,16,15,14,13,12,11,10,9,8,7,6,5,4,3,2,1,1,1",
                        "S_TurboFinishTime": True,
                    },
                },
                "rounds240": {
                    "aliases": [],
                    "script": {
                        "tm": "Rounds.Script.txt",
                        "tmnext": "Trackmania/TM_Rounds_Online.Script.txt",
                    },
                    "settings": {
                        "S_FinishTimeout": 10,
                        "S_PointsLimit": 240,
                        "S_WarmUpNb": 1,
                        "S_WarmUpDuration": 900,
                        "S_PointsRepartition": "50,45,41,38,36,34,32,30,28,26,24,22,20,18,16,15,14,13,12,11,10,9,8,7,6,5,4,3,2,1,1,1",
                        "S_TurboFinishTime": True,
                    },
                },
                "rounds480": {
                    "aliases": ["mxlc", "mxvc", "nac"],
                    "script": {
                        "tm": "Rounds.Script.txt",
                        "tmnext": "Trackmania/TM_Rounds_Online.Script.txt",
                    },
                    "settings": {
                        "S_FinishTimeout": 10,
                        "S_PointsLimit": 480,
                        "S_WarmUpNb": 1,
                        "S_WarmUpDuration": 600,
                        "S_PointsRepartition": "50,45,41,38,36,34,32,30,28,26,24,22,20,18,16,15,14,13,12,11,10,9,8,7,6,5,4,3,2,1,1,1",
                        "S_TurboFinishTime": True,
                    },
                },
                "laps50": {
                    "aliases": ["hec"],
                    "script": {
                        "tm": "Laps.Script.txt",
                        "tmnext": "Trackmania/TM_Laps_Online.Script.txt",
                    },
                    "settings": {
                        "S_FinishTimeout": 360,
                        "S_ForceLapsNb": 50,
                        "S_WarmUpNb": 1,
                        "S_WarmUpDuration": 600,
                    },
                },
                "timeattack": {
                    "aliases": ["ta"],
                    "script": {
                        "tm": "TimeAttack.Script.txt",
                        "tmnext": "Trackmania/TM_TimeAttack_Online.Script.txt",
                    },
                    "settings": {
                        "S_TimeLimit": 360,
                        "S_WarmUpNb": 0,
                        "S_WarmUpDuration": 0,
                    },
                },
            },
            "payouts": {
                "hec": [
                    1000,
                    700,
                    500,
                    400,
                    300,
                ],
                "smurfscup": [
                    6000,
                    4000,
                    3000,
                    2500,
                    1500,
                    1000,
                    800,
                    600,
                    400,
                    200,
                ],
            },
            "names": {
                "fallback": {
                    "name": "Fallback Cup (Not Configured)",
                    "preset_on": "rounds180",
                    "preset_off": "timeattack",
                    "map_count": 1,
                    "scoremode": "rounds_default",
                }
            },
        }
    return FALLBACK_CONFIG
