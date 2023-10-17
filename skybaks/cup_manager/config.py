import logging
import os
import json
import aiohttp
import re

from pyplanet.conf import settings
from pyplanet.core.instance import Instance
from pyplanet.contrib.command import Command
from pyplanet.contrib.setting import Setting

from .views import CupConfigView
from .utils.validation import validate_config


logger = logging.getLogger(__name__)

FALLBACK_CONFIG: "dict[str]" = dict()


class CupConfiguration:
    def __init__(self, app) -> None:
        self.app = app
        self.instance: Instance = app.instance
        self.config_path = "UserData/Maps/MatchSettings"
        self.config: "dict[str]" = dict()
        self.session: "aiohttp.ClientSession | None" = None
        try:
            self.config_path = settings.CUP_MANAGER_CONFIG_PATH
        except KeyError:
            logger.debug("CUP_MANAGER_CONFIG_PATH not defined in local.py")
        self.config_file = Setting(
            "cup_manager_config_filename",
            "Cup Manager Config Filename",
            Setting.CAT_GENERAL,
            type=str,
            description='Json filename to be loaded as cup configuration. Loads from folder "%s" which is configured by CUP_MANAGER_CONFIG_PATH in local.py'
            % self.config_path,
            default="cup_manager_config.json",
        )

    async def on_start(self) -> None:
        await self.create_session()
        await self.app.context.setting.register(self.config_file)
        await self.instance.command_manager.register(
            Command(
                command="config",
                aliases=["c"],
                namespace=self.app.namespace,
                target=self.command_config,
                admin=True,
                perms="cup:manage_cup",
                description="Load in a new configuration for the cup manager plugin",
            )
            .add_param(
                "command",
                nargs=1,
                type=str,
                required=False,
                help='"load" to load a config file; "download" to download a config file',
            )
            .add_param(
                "file_or_url",
                nargs=1,
                type=str,
                required=False,
                help="Filename or URL to load config from",
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
        config_filename: str = ""
        if not data.command:
            view = CupConfigView(self.app, self.config)
            return await view.display(player=player)
        elif data.command in ["load", "l"]:
            if data.file_or_url:
                config_filename = data.file_or_url
            else:
                config_filename = await self.config_file.get_value()
        elif data.command in ["download", "dl"]:
            if data.file_or_url:
                config_filename = await self.download_file(data.file_or_url, player)
        else:
            await self.instance.chat(
                f'$f00Unknown config command "{str(data.command)}". Use "load" or "l" to load a file or "download" or "dl" to download a file.',
                player.login,
            )
            return

        if config_filename:
            loaded_config = await self.load_config_from_file(config_filename, player)
            if loaded_config:
                self.config = loaded_config
                await self.config_file.set_value(config_filename)

    async def load_config_from_file(self, filename, player=None) -> dict:
        loaded_config = await self.load_json_from_config_dir(filename)
        if await self.check_config_valid(loaded_config):
            logger.info(f"Loaded cup configuration from {filename}")
            if player:
                await self.instance.chat(
                    f"$ff0Loaded cup configuration from {filename}", player.login
                )
            return loaded_config
        else:
            logger.error(f"Failed to load config from {filename}")
            if player:
                await self.instance.chat(
                    f"$f00Failed to load config from {filename}", player.login
                )
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
        loaded_config_file = await self.load_config_from_file(
            await self.config_file.get_value()
        )
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

    async def write_file_from_config_dir(self, filename: str, contents) -> None:
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

    async def create_session(self) -> None:
        self.session = await aiohttp.ClientSession(
            headers={"User-Agent": "https://github.com/skybaks/pyplanet-cup_manager"}
        ).__aenter__()

    async def close_session(self) -> None:
        if self.session and hasattr(self.session, "__aexist__"):
            await self.session.__aexit__()

    async def download_file(self, url: str, player=None) -> str:
        try:
            response = await self.session.get(url)
            if response.status < 200 or response.status > 399:
                if player:
                    self.instance.chat(
                        f"$f00Error downloading config from {url}", player.login
                    )
                logger.error(f"Got invalid response from download url {url}")
                return
            out_filename = await self.get_filename_from_url(url)
            await self.write_file_from_config_dir(out_filename, await response.read())
        except Exception as e:
            logger.error(f'Exception while trying to download from "{url}": {str(e)}')
            if player:
                await self.instance.chat(
                    f'$f00Error when trying to download from "{str(url)}"', player.login
                )
            return
        if player:
            self.instance.chat(f"$ff0Downloaded config to {out_filename}", player.login)
        return out_filename

    async def get_filename_from_url(self, url: str) -> str:
        filename: str = os.path.basename(url).replace(".json", "")
        filename = re.sub("[^a-zA-Z0-9]", "_", filename)
        if not filename:
            filename = os.path.dirname(url)
        if not filename.endswith(".json"):
            filename += ".json"
        return filename

    async def save_config_file(self, config: dict) -> str:
        config_filename = await self.config_file.get_value()
        try:
            await self.write_file_from_config_dir(config_filename, json.dumps(config, indent=4))
            self.config = config
            return config_filename
        except Exception as e:
            logger.exception(
                f"Error when saving config to file {config_filename}: " + str(e)
            )

    async def check_config_valid(self, config: dict, player=None) -> bool:
        invalid_reasons = validate_config(config)
        if invalid_reasons:
            logger.error("Config validation failed:")
            for reason in invalid_reasons:
                logger.error(f"\t{str(reason)}")
            if player:
                await self.app.instance.chat(
                    "$f00Config validation failed:", player.login
                )
                for reason in invalid_reasons:
                    await self.app.instance.chat(f"$f00\t{str(reason)}", player.login)
            return False
        else:
            logger.debug("Config validation passed")
            return True


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
                "basic": {
                    "name": "Basic Cup",
                    "preset_on": "rounds180",
                    "preset_off": "timeattack",
                    "map_count": 1,
                    "scoremode": "rounds_default",
                },
            },
        }
    return FALLBACK_CONFIG
