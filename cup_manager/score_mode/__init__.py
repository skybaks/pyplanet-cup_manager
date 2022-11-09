from .score_mode_base import ScoreNames, ScoreModeBase, ScoreModeFallback
from .score_rounds import ScoreRoundsDefault
from .score_timeattack import ScoreTimeAttackDefault
from .score_laps import ScoreLapsDefault

__all__ = [
	'ScoreNames',
	'ScoreModeBase',
	'ScoreModeFallback',
	'ScoreRoundsDefault',
	'ScoreTimeAttackDefault',
	'ScoreLapsDefault',
]


def get_sorting_from_mode(mode_script: str) -> ScoreModeBase:
	"""
	Returns a score sorting object based on the name of the mode script
	"""
	mode_script_lower = mode_script.lower()
	if 'timeattack' in mode_script_lower:
		return ScoreTimeAttackDefault()
	elif 'laps' in mode_script_lower:
		return ScoreLapsDefault()
	elif 'rounds' in mode_script_lower:
		return ScoreRoundsDefault()
	else:
		return ScoreModeFallback()
