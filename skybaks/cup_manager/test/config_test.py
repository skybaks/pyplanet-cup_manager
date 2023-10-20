import unittest
from ..config import get_fallback_config
from ..utils.validation import validate_config, ErrorCode, ConfigValidationError


class ConfigValidationTest(unittest.TestCase):
    def test_fallback_config(self) -> None:
        reasons = validate_config(get_fallback_config())
        self.assertFalse(reasons, msg="\n".join(reasons))

    def test_basic(self) -> None:
        config = {"presets": dict(), "payouts": dict(), "names": dict()}
        reasons = validate_config(config)
        self.assertEqual(len(reasons), 0, "Unexpected amount of invalid reason(s)")

        del config["presets"]
        reasons = validate_config(config)
        self.assertEqual(len(reasons), 1, "Unexpected amount of invalid reason(s)")
        self.assertEqual(ErrorCode.MISSING_FIELD, reasons[0].error_code)
        self.assertIn("presets", reasons[0].args)

        del config["payouts"]
        reasons = validate_config(config)
        self.assertEqual(len(reasons), 2, "Unexpected amount of invalid reason(s)")
        self.assertEqual(ErrorCode.MISSING_FIELD, reasons[1].error_code)
        self.assertIn("payouts", reasons[1].args)

        del config["names"]
        reasons = validate_config(config)
        self.assertEqual(len(reasons), 3, "Unexpected amount of invalid reason(s)")
        self.assertEqual(ErrorCode.MISSING_FIELD, reasons[2].error_code)
        self.assertIn("names", reasons[2].args)

    def test_payout_config(self) -> None:
        config = {
            "presets": dict(),
            "payouts": {"pay-01": [1, 2, 3, 4, 5, 6]},
            "names": dict(),
        }
        reasons = validate_config(config)
        self.assertEqual(len(reasons), 0, "Unexpected amount of invalid reason(s)")

        config["payouts"]["pay-02"] = 1
        reasons = validate_config(config)
        self.assertEqual(len(reasons), 1, "Unexpected amount of invalid reason(s)")
        self.assertEqual(ErrorCode.INVALID_TYPE, reasons[0].error_code)
        self.assertIn("pay-02", reasons[0].context)
        self.assertIsNotNone(str(reasons[0]))

        config["payouts"]["pay-02"] = [1, 2, "3"]
        reasons = validate_config(config)
        self.assertEqual(len(reasons), 1, "Unexpected amount of invalid reason(s)")
        self.assertEqual(ErrorCode.INVALID_SUBTYPE, reasons[0].error_code)
        self.assertIn("pay-02", reasons[0].context)
        self.assertIsNotNone(str(reasons[0]))

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
        self.assertEqual(len(reasons), 1, "Unexpected amount of invalid reason(s)")
        self.assertEqual(ErrorCode.INVALID_TYPE, reasons[0].error_code)
        self.assertIn("pre-02", reasons[0].context)
        self.assertIsNotNone(str(reasons[0]))

        config["presets"]["pre-02"] = dict()
        reasons = validate_config(config)
        self.assertEqual(len(reasons), 3, "Unexpected amount of invalid reason(s)")
        self.assertEqual(ErrorCode.MISSING_FIELD, reasons[0].error_code)
        self.assertIn("aliases", reasons[0].args)
        self.assertIsNotNone(str(reasons[0]))
        self.assertEqual(ErrorCode.MISSING_FIELD, reasons[1].error_code)
        self.assertIn("script", reasons[1].args)
        self.assertIsNotNone(str(reasons[1]))
        self.assertEqual(ErrorCode.MISSING_FIELD, reasons[2].error_code)
        self.assertIn("settings", reasons[2].args)
        self.assertIsNotNone(str(reasons[2]))

        config["presets"]["pre-02"] = {
            "aliases": 0,
            "script": {"tm": ""},
            "settings": dict(),
        }
        reasons = validate_config(config)
        self.assertEqual(len(reasons), 1, "Unexpected amount of invalid reason(s)")
        self.assertEqual(ErrorCode.INVALID_TYPE, reasons[0].error_code)
        self.assertIn("pre-02", reasons[0].context)
        self.assertIsNotNone(str(reasons[0]))

        config["presets"]["pre-02"] = {
            "aliases": [1, "p2"],
            "script": {"tm": ""},
            "settings": dict(),
        }
        reasons = validate_config(config)
        self.assertEqual(len(reasons), 1, "Unexpected amount of invalid reason(s)")
        self.assertEqual(ErrorCode.INVALID_SUBTYPE, reasons[0].error_code)
        self.assertIn("pre-02", reasons[0].context)
        self.assertIn("aliases", reasons[0].context)
        self.assertIsNotNone(str(reasons[0]))

        config["presets"]["pre-02"] = {
            "aliases": ["p2"],
            "script": 0,
            "settings": dict(),
        }
        reasons = validate_config(config)
        self.assertEqual(len(reasons), 1, "Unexpected amount of invalid reason(s)")
        self.assertEqual(ErrorCode.INVALID_TYPE, reasons[0].error_code)
        self.assertIn("pre-02", reasons[0].context)
        self.assertIn("script", reasons[0].context)
        self.assertIsNotNone(str(reasons[0]))

        config["presets"]["pre-02"] = {
            "aliases": ["p2"],
            "script": dict(),
            "settings": dict(),
        }
        reasons = validate_config(config)
        self.assertEqual(len(reasons), 1, "Unexpected amount of invalid reason(s)")
        self.assertEqual(ErrorCode.EMPTY_CONTAINER, reasons[0].error_code)
        self.assertIn("pre-02", reasons[0].context)
        self.assertIn("script", reasons[0].context)
        self.assertIsNotNone(str(reasons[0]))

        config["presets"]["pre-02"] = {
            "aliases": ["p2"],
            "script": {"fake": "script"},
            "settings": dict(),
        }
        reasons = validate_config(config)
        self.assertEqual(len(reasons), 1, "Unexpected amount of invalid reason(s)")
        self.assertEqual(ErrorCode.INVALID_GAME_IDENTIFIER, reasons[0].error_code)
        self.assertIn("pre-02", reasons[0].context)
        self.assertIn("script", reasons[0].context)
        self.assertIn("fake", reasons[0].context)
        self.assertIsNotNone(str(reasons[0]))

        config["presets"]["pre-02"] = {
            "aliases": ["p2"],
            "script": {"tmnext": 1},
            "settings": dict(),
        }
        reasons = validate_config(config)
        self.assertEqual(len(reasons), 1, "Unexpected amount of invalid reason(s)")
        self.assertEqual(ErrorCode.INVALID_TYPE, reasons[0].error_code)
        self.assertIn("pre-02", reasons[0].context)
        self.assertIn("script", reasons[0].context)
        self.assertIn("tmnext", reasons[0].context)
        self.assertIsNotNone(str(reasons[0]))

        config["presets"]["pre-02"] = {
            "aliases": ["p2"],
            "script": {"tmnext": "script"},
            "settings": 1,
        }
        reasons = validate_config(config)
        self.assertEqual(len(reasons), 1, "Unexpected amount of invalid reason(s)")
        self.assertEqual(ErrorCode.INVALID_TYPE, reasons[0].error_code)
        self.assertIn("pre-02", reasons[0].context)
        self.assertIn("settings", reasons[0].context)
        self.assertIsNotNone(str(reasons[0]))

    def test_names_config(self) -> None:
        config = {
            "presets": {
                "pre-1": {
                    "aliases": [],
                    "script": {"tm": "script.Script.txt"},
                    "settings": {"S_Setting": True},
                }
            },
            "payouts": {"pay-1": [0, 1, 2, 3]},
            "names": {"cup-1": {"name": "Cup 1"}},
        }
        reasons = validate_config(config)
        self.assertFalse(reasons)

        config["names"]["cup-2"] = list()
        reasons = validate_config(config)
        self.assertTrue(len(reasons) == 1)
        self.assertTrue("names/cup-2 is not the right type" in reasons[0])

        config["names"]["cup-2"] = dict()
        reasons = validate_config(config)
        self.assertTrue(len(reasons) == 1)
        self.assertTrue('"name" is missing from names/cup-2' in reasons[0])

        config["names"]["cup-2"] = {"name": 234.15}
        reasons = validate_config(config)
        self.assertTrue(len(reasons) == 1)
        self.assertTrue("names/cup-2/name is not the right type" in reasons[0])

        config["names"]["cup-2"] = {"name": "Cup 2", "map_count": "3"}
        reasons = validate_config(config)
        self.assertTrue(len(reasons) == 1)
        self.assertTrue("names/cup-2/map_count is not the right type" in reasons[0])

        config["names"]["cup-2"]["map_count"] = 3
        config["names"]["cup-2"]["scoremode"] = 6
        reasons = validate_config(config)
        self.assertEqual(len(reasons), 1)
        self.assertTrue("names/cup-2/scoremode is not the right type" in reasons[0])

        config["names"]["cup-2"]["scoremode"] = "fake_mode"
        reasons = validate_config(config)
        self.assertEqual(len(reasons), 1)
        self.assertTrue('names/cup-2/scoremode value of "fake_mode"' in reasons[0])

        config["names"]["cup-2"]["scoremode"] = "rounds_default"
        config["names"]["cup-2"]["payout"] = 1.25
        reasons = validate_config(config)
        self.assertEqual(len(reasons), 1)
        self.assertTrue("names/cup-2/payout is not the right type" in reasons[0])

        config["names"]["cup-2"]["payout"] = "fake_pay"
        reasons = validate_config(config)
        self.assertEqual(len(reasons), 1)
        self.assertTrue("names/cup-2/payout value of" in reasons[0])

        config["names"]["cup-2"]["payout"] = "pay-1"
        config["names"]["cup-2"]["preset_on"] = 0.0
        reasons = validate_config(config)
        self.assertEqual(len(reasons), 1)
        self.assertTrue("names/cup-2/preset_on is not the right type" in reasons[0])

        config["names"]["cup-2"]["preset_on"] = "preset_fake"
        reasons = validate_config(config)
        self.assertEqual(len(reasons), 1)
        self.assertTrue("names/cup-2/preset_on value of" in reasons[0])

        config["names"]["cup-2"]["preset_on"] = "pre-1"
        config["names"]["cup-2"]["preset_off"] = 0.0
        reasons = validate_config(config)
        self.assertEqual(len(reasons), 1)
        self.assertTrue("names/cup-2/preset_off is not the right type" in reasons[0])

        config["names"]["cup-2"]["preset_off"] = "preset_fake"
        reasons = validate_config(config)
        self.assertEqual(len(reasons), 1)
        self.assertTrue("names/cup-2/preset_off value of" in reasons[0])

        config["names"]["cup-2"]["preset_off"] = "pre-1"
        reasons = validate_config(config)
        self.assertEqual(len(reasons), 0)


if __name__ == "__main__":
    unittest.main()
