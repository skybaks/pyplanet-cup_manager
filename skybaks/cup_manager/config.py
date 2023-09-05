import logging

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
        # - look for config path in setting or env
        #   - if yes then use for storage
        # - else try to use local.py
        # - else try use default path for json
        # - else use fallback configs

    async def get_cup_presets(self) -> "dict[str, dict]":
        try:
            return settings.CUP_MANAGER_PRESETS
        except KeyError:
            logger.debug("CUP_MANAGER_PRESETS not defined in local.py")
        return get_fallback_presets()

    async def get_cup_payouts(self) -> "dict[str, dict]":
        try:
            return settings.CUP_MANAGER_PAYOUTS
        except KeyError:
            logger.debug("CUP_MANAGER_PAYOUTS not defined in local.py")
        return get_fallback_payouts()

    async def get_cup_settings(self) -> "dict[str, dict]":
        try:
            return settings.CUP_MANAGER_NAMES
        except KeyError:
            logger.debug("CUP_MANAGER_NAMES not defined in local.py")
        return get_fallback_names()


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
