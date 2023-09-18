import unittest
from ..config import validate_config, get_fallback_config


class ConfigValidationTest(unittest.TestCase):
    def test_fallback_config(self) -> None:
        reasons = validate_config(get_fallback_config())
        self.assertFalse(reasons, msg="\n".join(reasons))

    def test_basic(self) -> None:
        config = {"presets": dict(), "payouts": dict(), "names": dict()}
        reasons = validate_config(config)
        self.assertFalse(reasons, msg="\n".join(reasons))

    def test_failed_names_payout(self) -> None:
        config = {
            "presets": {},
            "payouts": {"test1": [1, 2]},
            "names": {"tc": {"name": "test cup", "payout": "test2"}},
        }
        reasons = validate_config(config)
        self.assertTrue(len(reasons) == 1)
        self.assertTrue("names/tc/payout" in reasons[0])

    def test_failed_names_preset(self) -> None:
        config = {
            "presets": {
                "pre-1": {
                    "aliases": [],
                    "script": {"tm": "Script.Script.txt"},
                    "settings": {"S_Setting": True},
                },
                "pre-2": {
                    "aliases": [],
                    "script": {"tmnext": "Other.Script.txt"},
                    "settings": {"S_Setting_1": 1},
                },
            },
            "payouts": dict(),
            "names": {
                "cup-1": {"name": "Cup 1", "preset_on": "pre-3", "preset_off": "pre-1"}
            },
        }
        reasons = validate_config(config)
        self.assertTrue(len(reasons) == 1)
        self.assertTrue("names/cup-1/preset_on" in reasons[0])


if __name__ == "__main__":
    unittest.main()
