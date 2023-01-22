import logging

from .score_base import ScoreModeBase
from .score_timeattack import ScoreTimeAttackDefault
from .score_laps import ScoreLapsDefault
from .score_rounds import ScoreRoundsDefault
from .score_cup import ScoreCupDefault
from .score_fallback import ScoreModeFallback


logger = logging.getLogger(__name__)


def get_sorting_from_mode_singular(mode_script: str) -> ScoreModeBase:
	"""
	Returns the default sorting mode of the input mode script
	"""
	mode_name = mode_script.lower()
	if 'timeattack' in mode_name:
		return ScoreTimeAttackDefault()
	elif 'laps' in mode_name:
		return ScoreLapsDefault()
	elif 'rounds' in mode_name:
		return ScoreRoundsDefault()
	elif 'cup' in mode_name:
		return ScoreCupDefault()
	else:
		return ScoreModeFallback()
