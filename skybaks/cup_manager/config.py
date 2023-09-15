import logging
import os
import json

from pyplanet.conf import settings
from pyplanet.core.instance import Instance


logger = logging.getLogger(__name__)

FALLBACK_CONFIG_PRESETS: dict = dict()
FALLBACK_CONFIG_PAYOUTS: dict = dict()
FALLBACK_CONFIG_NAMES: dict = dict()


class CupConfiguration:
    def __init__(self, app) -> None:
        self.app = app
        self.instance: Instance = app.instance
        self.cached_cup_presets: dict = dict()
        self.cached_cup_payouts: dict = dict()
        self.cached_cup_settings: dict = dict()
        self.config_path = "UserData/Maps/MatchSettings"
        try:
            self.config_path = settings.CUP_MANAGER_CONFIG_PATH
        except KeyError:
            logger.debug("CUP_MANAGER_CONFIG_PATH not defined in local.py")

    async def on_start(self) -> None:
        pass

    async def get_cup_presets(self, force_reload=False) -> "dict[str, dict]":
        if force_reload:
            self.cached_cup_presets = dict()
        if not self.cached_cup_presets:
            loaded_presets = await self.load_json_from_config("cup_presets.json")
            if loaded_presets:
                self.cached_cup_presets = loaded_presets
        if not self.cached_cup_presets:
            try:
                loaded_presets = settings.CUP_MANAGER_PRESETS
                if loaded_presets:
                    self.cached_cup_presets = loaded_presets
            except KeyError:
                logger.debug("CUP_MANAGER_PRESETS not defined in local.py")
        if not self.cached_cup_presets:
            self.cached_cup_presets = get_fallback_presets()
        return self.cached_cup_presets

    async def get_cup_payouts(self, force_reload=False) -> "dict[str, dict]":
        if force_reload:
            self.cached_cup_payouts = dict()
        if not self.cached_cup_payouts:
            loaded_payouts = await self.load_json_from_config("cup_payouts.json")
            if loaded_payouts:
                self.cached_cup_payouts = loaded_payouts
        if not self.cached_cup_payouts:
            try:
                loaded_payouts = settings.CUP_MANAGER_PAYOUTS
                if loaded_payouts:
                    self.cached_cup_payouts = loaded_payouts
            except KeyError:
                logger.debug("CUP_MANAGER_PAYOUTS not defined in local.py")
        if not self.cached_cup_payouts:
            self.cached_cup_payouts = get_fallback_payouts()
        return self.cached_cup_payouts

    async def get_cup_settings(self, force_reload=False) -> "dict[str, dict]":
        if force_reload:
            self.cached_cup_settings = dict()
        if not self.cached_cup_settings:
            loaded_settings = await self.load_json_from_config("cup_settings.json")
            if loaded_settings:
                self.cached_cup_settings = loaded_settings
        if not self.cached_cup_settings:
            try:
                loaded_settings = settings.CUP_MANAGER_NAMES
                if loaded_settings:
                    self.cached_cup_settings = loaded_settings
            except KeyError:
                logger.debug("CUP_MANAGER_NAMES not defined in local.py")
        if not self.cached_cup_settings:
            self.cached_cup_settings = get_fallback_names()
        return self.cached_cup_settings

    async def read_file_from_config(self, filename: str) -> str:
        file_path = os.path.join(self.config_path, filename)
        try:
            if await self.instance.storage.driver.exists(file_path):
                async with self.instance.storage.driver.open(file_path, "r") as r_file:
                    return await r_file.read()
        except Exception as e:
            logger.exception(e)
        return ""

    async def write_file_from_config(self, filename: str, contents: str) -> None:
        file_path = os.path.join(self.config_path, filename)
        try:
            async with self.instance.storage.driver.open(file_path, "w") as w_file:
                await w_file.write(contents)
        except Exception as e:
            logger.exception(e)

    async def load_json_from_config(self, filename: str) -> dict:
        file_contents = await self.read_file_from_config(filename)
        if file_contents:
            try:
                return json.loads(file_contents)
            except:
                logger.error("Error decoding json file " + filename)
        return dict()


def get_fallback_presets() -> "dict[str, dict]":
    global FALLBACK_CONFIG_PRESETS
    if not FALLBACK_CONFIG_PRESETS:
        logger.debug("Initializing fallback config presets")
        FALLBACK_CONFIG_PRESETS = {
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
        }
    return FALLBACK_CONFIG_PRESETS


def get_fallback_payouts() -> "dict[str, dict]":
    global FALLBACK_CONFIG_PAYOUTS
    if not FALLBACK_CONFIG_PAYOUTS:
        logger.debug("Initializing fallback payouts")
        FALLBACK_CONFIG_PAYOUTS = {
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
        }
    return FALLBACK_CONFIG_PAYOUTS


def get_fallback_names() -> "dict[str, dict]":
    global FALLBACK_CONFIG_NAMES
    if not FALLBACK_CONFIG_NAMES:
        logger.debug("Initializing fallback names")
        FALLBACK_CONFIG_NAMES = {
            "fallback": {
                "name": "Fallback Cup (Not Configured)",
                "preset_on": "rounds180",
                "preset_off": "timeattack",
                "map_count": 1,
                "scoremode": "rounds_default",
            }
        }
    return FALLBACK_CONFIG_NAMES
