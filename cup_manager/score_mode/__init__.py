import logging

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

logger = logging.getLogger(__name__)


def get_sorting_from_mode(mode_script: 'str | list[str]') -> ScoreModeBase:
	"""
	Returns a score sorting object based on the name of the mode script
	"""
	mode_names = []	# type: list[str]
	if isinstance(mode_script, list):
		mode_names = list(set([name.lower() for name in mode_script]))
	elif isinstance(mode_script, str):
		mode_names.append(mode_script.lower())
	else:
		logger.error("Unexpected type in get_sorting_from_mode: " + str(mode_script))

	if len(mode_names) < 1:
		return ScoreModeFallback()
	elif len(mode_names) == 1:
		mode_name = mode_names[0]
		if 'timeattack' in mode_name:
			return ScoreTimeAttackDefault()
		elif 'laps' in mode_name:
			return ScoreLapsDefault()
		elif 'rounds' in mode_name:
			return ScoreRoundsDefault()
		else:
			return ScoreModeFallback()
	else:
		return ScoreModeFallback()
