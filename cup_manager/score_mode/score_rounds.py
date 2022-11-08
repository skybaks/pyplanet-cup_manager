import logging

from ..app_types import TeamPlayerScore
from ..models import MatchInfo
from .score_mode_base import ScoreModeBase

logger = logging.getLogger(__name__)


class ScoreRoundsDefault(ScoreModeBase):
	"""
	Score sorting for Rounds mode.
	Sorting: Points descending
	"""

	def __init__(self) -> None:
		super().__init__()
		self.name = 'rounds_default'
		self.score1_is_time = False
		self.score2_is_time = False
		self.scoreteam_is_time = False
		self.use_score1 = True
		self.use_score2 = False
		self.use_scoreteam = False
		self.score_names.score1_name = 'Points'


	def combine_scores(self, scores: 'list[list[TeamPlayerScore]]', maps: 'list[list[MatchInfo]]'=None, **kwargs) -> 'list[TeamPlayerScore]':
		combined_scores = []	# type: list[TeamPlayerScore]
		for map_scores in scores:
			for map_score in map_scores:
				existing_score = next((x for x in combined_scores if x.login == map_score.login), None)
				if existing_score:
					existing_score.player_score += map_score.player_score
				else:
					combined_scores.append(map_score)
		return combined_scores


	def sort_scores(self, scores: 'list[TeamPlayerScore]') -> 'list[TeamPlayerScore]':
		return sorted(scores, key=lambda x: (-x.player_score))


	def update_placements(self, scores: 'list[TeamPlayerScore]') -> 'list[TeamPlayerScore]':
		for i in range(0, len(scores)):
			if i > 0:
				if scores[i-1].player_score == scores[i].player_score:
					scores[i].placement = scores[i-1].placement
				else:
					scores[i].placement = i+1
			else:
				scores[i].placement = i+1
		return scores
