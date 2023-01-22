import logging

from ..app_types import TeamPlayerScore
from ..models import MatchInfo
from .score_base import ScoreModeBase

logger = logging.getLogger(__name__)

class ScoreCupDefault(ScoreModeBase):
	"""
	Score sorting for Cup mode. This mode will be used by default for mode
	scripts with "Cup" in their name.

	It uses only the match points of each individual player sorted in descending
	order.


	Recommended Modes: Cup
	Sorting: Points descending
	"""

	def __init__(self) -> None:
		super().__init__()
		self.name = 'cup_default'
		self.display_name = 'Default Cup Mode'
		self.brief = 'Default sorting mode for Cup'
		self.score1_is_time = False
		self.score2_is_time = False
		self.scoreteam_is_time = False
		self.use_score1 = True
		self.use_score2 = False
		self.use_scoreteam = False
		self.score_names.score1_name = 'Point(s)'


	def combine_scores(self, scores: 'list[list[TeamPlayerScore]]', maps: 'list[MatchInfo]' = ..., **kwargs) -> 'list[TeamPlayerScore]':
		combined_scores: 'list[TeamPlayerScore]' = []
		for map_scores in scores:
			for map_score in map_scores:
				existing_score = next((x for x in combined_scores if x.login == map_score.login), None)
				# Use player_score to hold the match_score to simplify needing
				# to update display and output methods
				if existing_score and existing_score.player_score < map_score.player_score_match:
					existing_score.player_score = map_score.player_score_match
				else:
					map_score.player_score = map_score.player_score_match
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
