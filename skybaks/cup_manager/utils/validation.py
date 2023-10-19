from enum import Enum
from ..score_mode import SCORE_MODE


class ErrorCode(Enum):
    INVALID_TYPE = 1000
    INVALID_SUBTYPE = 1100
    INVALID_GAME_IDENTIFIER = 1200
    MISSING_FIELD = 2000
    EMPTY_CONTAINER = 3000


class ConfigValidationError:
    def __init__(self, error_code: ErrorCode, context: str, *args) -> None:
        self.error_code: ErrorCode = error_code
        self.context: str = context
        self.args = args

    def __str__(self) -> str:
        context_str = " | ".join(self.context)
        if self.error_code == ErrorCode.INVALID_TYPE:
            return "$<%s$> is not the right type. Expected %s" % (
                (context_str,) + self.args
            )
        elif self.error_code == ErrorCode.INVALID_SUBTYPE:
            return (
                "$<%s$> contains elements which are not the right type. Expected %s"
                % ((context_str,) + self.args)
            )
        elif self.error_code == ErrorCode.INVALID_GAME_IDENTIFIER:
            return "$<%s$> is not a valid game identifier" % (
                (context_str,) + self.args
            )
        elif self.error_code == ErrorCode.MISSING_FIELD:
            return '$<%s$> is missing field "%s"' % ((context_str,) + self.args)
        elif self.error_code == ErrorCode.EMPTY_CONTAINER:
            return "$<%s$> contains no elements. %s" % ((context_str,) + self.args)


def validate_presets(config: dict) -> "list[ConfigValidationError]":
    invalid_reasons: "list[str]" = list()
    config_presets = config.get("presets")
    context_base: "list[str]" = ["presets"]
    if not isinstance(config_presets, dict):
        invalid_reasons.append(
            ConfigValidationError(ErrorCode.INVALID_TYPE, context_base, "dict")
        )
    else:
        for key, data in config_presets.items():
            if not isinstance(data, dict):
                invalid_reasons.append(
                    ConfigValidationError(
                        ErrorCode.INVALID_TYPE, context_base + [key], "dict"
                    )
                )
            else:
                if "aliases" not in data:
                    invalid_reasons.append(
                        ConfigValidationError(
                            ErrorCode.MISSING_FIELD, context_base + [key], "aliases"
                        )
                    )
                else:
                    data_aliases = data.get("aliases")
                    if not isinstance(data_aliases, list):
                        invalid_reasons.append(
                            ConfigValidationError(
                                ErrorCode.INVALID_TYPE,
                                context_base + [key, "aliases"],
                                "list",
                            )
                        )
                    else:
                        if any(not isinstance(elem, str) for elem in data_aliases):
                            invalid_reasons.append(
                                ConfigValidationError(
                                    ErrorCode.INVALID_SUBTYPE,
                                    context_base + [key, "aliases"],
                                    "str",
                                )
                            )

                if "script" not in data:
                    invalid_reasons.append(
                        ConfigValidationError(
                            ErrorCode.MISSING_FIELD, context_base + [key], "script"
                        )
                    )
                else:
                    script_data = data.get("script")
                    if not isinstance(script_data, dict):
                        invalid_reasons.append(
                            ConfigValidationError(
                                ErrorCode.INVALID_TYPE,
                                context_base + [key, "script"],
                                "dict",
                            )
                        )
                    else:
                        if not script_data:
                            invalid_reasons.append(
                                ConfigValidationError(
                                    ErrorCode.EMPTY_CONTAINER,
                                    context_base + [key, "script"],
                                    "Define a script for at least one game",
                                )
                            )
                        else:
                            for game, script_name in script_data.items():
                                if game not in ["tm", "tmnext", "sm"]:
                                    invalid_reasons.append(
                                        ConfigValidationError(
                                            ErrorCode.INVALID_GAME_IDENTIFIER,
                                            context_base + [key, "script", game],
                                        )
                                    )
                                if not isinstance(script_name, str):
                                    invalid_reasons.append(
                                        ConfigValidationError(
                                            ErrorCode.INVALID_TYPE,
                                            context_base + [key, "script", game],
                                            "str",
                                        )
                                    )

                if "settings" not in data:
                    invalid_reasons.append(
                        ConfigValidationError(
                            ErrorCode.MISSING_FIELD, context_base + [key], "settings"
                        )
                    )
                else:
                    settings_data = data.get("settings")
                    if not isinstance(settings_data, dict):
                        invalid_reasons.append(
                            ConfigValidationError(
                                ErrorCode.INVALID_TYPE,
                                context_base + [key, "settings"],
                                "dict",
                            )
                        )

    return invalid_reasons


def validate_payouts(config: dict) -> "list[str]":
    invalid_reasons: "list[str]" = list()
    config_payouts = config.get("payouts")
    if not isinstance(config_payouts, dict):
        invalid_reasons.append("payouts config is not the right type. Expected a dict")
    else:
        for key, data in config_payouts.items():
            if not isinstance(data, list):
                invalid_reasons.append(
                    f"$<$fffpayouts | {key}$> is not the right type. Expected a list"
                )
            else:
                if any(not isinstance(elem, int) for elem in data):
                    invalid_reasons.append(
                        f"$<$fffpayouts | {key}$> contains elements which are not the right type. Expected int"
                    )
    return invalid_reasons


def validate_names(config: dict) -> "list[str]":
    invalid_reasons: "list[str]" = list()
    config_names = config.get("names")
    if not isinstance(config_names, dict):
        invalid_reasons.append("names config is not the right type. Expected a dict")
    else:
        for key, data in config_names.items():
            if not isinstance(data, dict):
                invalid_reasons.append(
                    f"$<$fffnames | {key}$> is not the right type. Expected a dict"
                )
            else:
                if "name" not in data:
                    invalid_reasons.append(
                        f'"name" is missing from $<$fffnames | {key}$>'
                    )
                else:
                    if not isinstance(data.get("name"), str):
                        invalid_reasons.append(
                            f"$<$fffnames | {key} | name$> is not the right type. Expected a string"
                        )

                if "map_count" in data and not isinstance(data.get("map_count"), int):
                    invalid_reasons.append(
                        f"$<$fffnames | {key} | map_count$> is not the right type. Expected an int"
                    )

                if "scoremode" in data:
                    data_scoremode = data.get("scoremode")
                    if not isinstance(data_scoremode, str):
                        invalid_reasons.append(
                            f"$<$fffnames | {key} | scoremode$> is not the right type. Expected a string"
                        )
                    else:
                        if data_scoremode not in SCORE_MODE:
                            invalid_reasons.append(
                                f'$<$fffnames | {key} | scoremode$> value of "{str(data_scoremode)}" does not match an existing score mode'
                            )

                if "payout" in data:
                    data_payout = data.get("payout")
                    if not isinstance(data_payout, str):
                        invalid_reasons.append(
                            f"$<$fffnames | {key} | payout$> is not the right type. Expected a string"
                        )
                    else:
                        if data_payout not in config.get("payouts", dict()):
                            invalid_reasons.append(
                                f'$<$fffnames | {key} | payout$> value of "{str(data_payout)}" does not match an existing payout'
                            )

                if "preset_on" in data:
                    data_preset_on = data.get("preset_on")
                    if not isinstance(data_preset_on, str):
                        invalid_reasons.append(
                            f"$<$fffnames | {key} | preset_on$> is not the right type. Expected a string"
                        )
                    else:
                        if data_preset_on not in config.get("presets", dict()):
                            aliases = list()
                            for preset_key, preset_val in config.get(
                                "presets", dict()
                            ).items():
                                aliases += preset_val.get("aliases", list())
                            if data_preset_on not in aliases:
                                invalid_reasons.append(
                                    f'$<$fffnames | {key} | preset_on$> value of "{str(data_preset_on)}" does not match an existing preset'
                                )

                if "preset_off" in data:
                    data_preset_off = data.get("preset_off")
                    if not isinstance(data_preset_off, str):
                        invalid_reasons.append(
                            f"$<$fffnames | {key} | preset_off$> is not the right type. Expected a string"
                        )
                    else:
                        if data_preset_off not in config.get("presets", dict()) and (
                            "presets" in config
                            and "aliases" in config["presets"]
                            and data_preset_off not in config["presets"]["aliases"]
                        ):
                            invalid_reasons.append(
                                f'$<$fffnames | {key} | preset_off$> value of "{str(data_preset_off)}" does not match an existing preset'
                            )

    return invalid_reasons


def validate_config(config: dict) -> "list[ConfigValidationError]":
    invalid_reasons: "list[ConfigValidationError]" = list()
    if not isinstance(config, dict):
        invalid_reasons.append("Input config is not the right type. Expected a dict")
    else:
        if "presets" not in config:
            invalid_reasons.append('"presets" entry is missing from config')
        else:
            invalid_reasons += validate_presets(config)

        if "payouts" not in config:
            invalid_reasons.append('"payouts" entry is missing from config')
        else:
            invalid_reasons += validate_payouts(config)

        if "names" not in config:
            invalid_reasons.append('"names" entry is missing from config')
        else:
            invalid_reasons += validate_names(config)
    return invalid_reasons
