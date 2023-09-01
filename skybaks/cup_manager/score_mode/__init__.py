from .score_base import ScoreNames, ScoreModeBase
from .score_rounds import ScoreRoundsDefault
from .score_timeattack import ScoreTimeAttackDefault, ScoreTimeAttackPenaltyAuthorPlus15
from .score_laps import ScoreLapsDefault
from .score_fallback import ScoreModeFallback
from .score_mixed import ScoreModeMixed


__all__ = [
    "ScoreNames",
    "ScoreModeBase",
    "ScoreRoundsDefault",
    "ScoreTimeAttackDefault",
    "ScoreTimeAttackPenaltyAuthorPlus15",
    "ScoreLapsDefault",
    "ScoreModeFallback",
    "ScoreModeMixed",
]


def _build_mode_score_dict() -> "dict[str, type[ScoreModeBase]]":
    mode_scores = {}  # type: dict[str, any]
    lookup_classes = [ScoreModeBase]
    while lookup_classes:
        parent_class = lookup_classes.pop()
        for child_class in parent_class.__subclasses__():
            lookup_classes.append(child_class)
            child_instance = child_class()
            if child_instance.name not in mode_scores:
                mode_scores[child_instance.name] = child_class
    return mode_scores


SCORE_MODE = {}
if not SCORE_MODE:
    SCORE_MODE = _build_mode_score_dict()
