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

        del config["presets"]
        reasons = validate_config(config)
        self.assertTrue(len(reasons) == 1)
        self.assertTrue("presets" in reasons[0])

        del config["payouts"]
        reasons = validate_config(config)
        self.assertTrue(len(reasons) == 2)
        self.assertTrue("payouts" in reasons[1])

        del config["names"]
        reasons = validate_config(config)
        self.assertTrue(len(reasons) == 3)
        self.assertTrue("names" in reasons[2])

    def test_payout_config(self) -> None:
        config = {
            "presets": dict(),
            "payouts": {"pay-01": [1, 2, 3, 4, 5, 6]},
            "names": dict(),
        }
        reasons = validate_config(config)
        self.assertFalse(reasons)

        config["payouts"]["pay-02"] = 1
        reasons = validate_config(config)
        self.assertTrue(len(reasons) == 1)
        self.assertTrue("payouts/pay-02 is not the right type" in reasons[0])

        config["payouts"]["pay-02"] = [1, 2, "3"]
        reasons = validate_config(config)
        self.assertTrue(len(reasons) == 1)
        self.assertTrue("payouts/pay-02 contains elements which are not" in reasons[0])

    def test_presets_config(self) -> None:
        config = {
            "presets": {
                "pre-01": {
                    "aliases": list(),
                    "script": {"tm": "script.Script.txt"},
                    "settings": dict(),
                }
            },
            "payouts": dict(),
            "names": dict(),
        }
        reasons = validate_config(config)
        self.assertFalse(reasons)

        config["presets"]["pre-02"] = 1
        reasons = validate_config(config)
        self.assertTrue(len(reasons) == 1)
        self.assertTrue("presets/pre-02 is not the right type" in reasons[0])

        config["presets"]["pre-02"] = dict()
        reasons = validate_config(config)
        self.assertTrue(len(reasons) == 3)
        self.assertTrue("aliases" in reasons[0])
        self.assertTrue("script" in reasons[1])
        self.assertTrue("settings" in reasons[2])

        config["presets"]["pre-02"] = {
            "aliases": 0,
            "script": {"tm": ""},
            "settings": dict(),
        }
        reasons = validate_config(config)
        self.assertTrue(len(reasons) == 1)
        self.assertTrue("presets/pre-02/aliases is not the right type" in reasons[0])

        config["presets"]["pre-02"] = {
            "aliases": [1, "p2"],
            "script": {"tm": ""},
            "settings": dict(),
        }
        reasons = validate_config(config)
        self.assertTrue(len(reasons) == 1)
        self.assertTrue(
            "presets/pre-02/aliases contains elements which are not the right type"
            in reasons[0]
        )

        config["presets"]["pre-02"] = {
            "aliases": ["p2"],
            "script": 0,
            "settings": dict(),
        }
        reasons = validate_config(config)
        self.assertTrue(len(reasons) == 1)
        self.assertTrue("presets/pre-02/script is not the right type" in reasons[0])

        config["presets"]["pre-02"] = {
            "aliases": ["p2"],
            "script": dict(),
            "settings": dict(),
        }
        reasons = validate_config(config)
        self.assertTrue(len(reasons) == 1)
        self.assertTrue("presets/pre-02/script contains no elements" in reasons[0])

        config["presets"]["pre-02"] = {
            "aliases": ["p2"],
            "script": {"fake": "script"},
            "settings": dict(),
        }
        reasons = validate_config(config)
        self.assertTrue(len(reasons) == 1)
        self.assertTrue("presets/pre-02/script/fake is not a valid game" in reasons[0])

        config["presets"]["pre-02"] = {
            "aliases": ["p2"],
            "script": {"tmnext": 1},
            "settings": dict(),
        }
        reasons = validate_config(config)
        self.assertTrue(len(reasons) == 1)
        self.assertTrue("presets/pre-02/script/tmnext value of" in reasons[0])

        config["presets"]["pre-02"] = {
            "aliases": ["p2"],
            "script": {"tmnext": "script"},
            "settings": 1,
        }
        reasons = validate_config(config)
        self.assertTrue(len(reasons) == 1)
        self.assertTrue("presets/pre-02/settings is not the right type" in reasons[0])

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
