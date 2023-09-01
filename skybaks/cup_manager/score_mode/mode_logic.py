import logging

from .score_base import ScoreModeBase
from .score_fallback import ScoreModeFallback
from .score_mixed import ScoreModeMixed
from .mode_logic_singular import get_sorting_from_mode_singular


logger = logging.getLogger(__name__)


def get_sorting_from_mode(mode_script: "str | list[str]") -> ScoreModeBase:
    """
    Returns a score sorting object based on the name of the mode script(s)
    """
    mode_names = []  # type: list[str]
    if isinstance(mode_script, list):
        mode_names = list(set([name.lower() for name in mode_script]))
    elif isinstance(mode_script, str):
        mode_names.append(mode_script.lower())
    else:
        logger.error("Unexpected type in get_sorting_from_mode: " + str(mode_script))

    if len(mode_names) < 1:
        return ScoreModeFallback()
    elif len(mode_names) == 1:
        return get_sorting_from_mode_singular(mode_names[0])
    else:
        return ScoreModeMixed()
