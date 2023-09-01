import logging

from ..app_types import TeamPlayerScore
from ..models import MatchInfo
from .score_base import ScoreModeBase
from .mode_logic_singular import get_sorting_from_mode_singular


class ScoreModeMixed(ScoreModeBase):
	"""
	Score sorting for mixed mode scripts. This mode will be used by default when
	combining scores across multiple maps that use different mode scripts.

	It works by performing the default score sorting for each map individually,
	then giving out "Placement Points" to each player based on their ranking in
	the map. All the "Placement Points" for a player are summed across all maps
	and then the scores are re-sorted to determine final rankings.

	"Placement Points" are allocated using the number of players in the map as
	the point value given to the highest ranked player. Then each player down
	the rankings gets 1 less point than the player ranked above them.


	Recommended Modes: Any combination that have their own default sorting mode
	Sorting: Points for each map placement descending
	"""

	def __init__(self) -> None:
		super().__init__()
		self.name = 'score_mode_mixed'
		self.display_name = 'Default Mixed Modes'
		self.brief = 'Use placement as points to combine mixed mode results'
		self.score1_is_time = False
		self.score2_is_time = False
		self.scoreteam_is_time = False
		self.use_score1 = True
		self.use_score2 = False
		self.use_scoreteam = False
		self.score_names.score1_name = 'Placement Pt(s)'


	def combine_scores(self, scores: 'list[list[TeamPlayerScore]]', maps: 'list[MatchInfo]'=[], **kwargs) -> 'list[TeamPlayerScore]':
		combined_scores = []	# type: list[TeamPlayerScore]
		for map_scores, map_info in zip(scores, maps):
			map_sorting = get_sorting_from_mode_singular(map_info.mode_script)
			map_scores_sorted = map_sorting.sort_scores(map_scores)
			map_scores_sorted = map_sorting.update_placements(map_scores_sorted)
			for map_score in map_scores_sorted:
				map_score.player_score = len(map_scores_sorted) - map_score.placement + 1
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
