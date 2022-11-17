import logging

from ..app_types import TeamPlayerScore
from ..models import MatchInfo
from .score_base import ScoreModeBase

logger = logging.getLogger(__name__)


class ScoreTimeAttackDefault(ScoreModeBase):
	"""
	Score sorting for TimeAttack mode.
	Sorting: Maps played descending, Summed finish time ascending
	"""

	def __init__(self) -> None:
		super().__init__()
		self.name = 'timeattack_default'
		self.score1_is_time = True
		self.score2_is_time = False
		self.scoreteam_is_time = False
		self.use_score1 = True
		self.use_score2 = False
		self.use_scoreteam = False
		self.score_names.score1_name = 'Time'


	def combine_scores(self, scores: 'list[list[TeamPlayerScore]]', maps: 'list[MatchInfo]'=[], **kwargs) -> 'list[TeamPlayerScore]':
		combined_scores = []	# type: list[TeamPlayerScore]
		for map_scores in scores:
			for map_score in map_scores:
				existing_score = next((x for x in combined_scores if x.login == map_score.login), None)
				if existing_score:
					existing_score.count += 1
					existing_score.player_score += map_score.player_score
				else:
					map_score.count = 1
					combined_scores.append(map_score)
		return combined_scores


	def sort_scores(self, scores: 'list[TeamPlayerScore]') -> 'list[TeamPlayerScore]':
		return sorted(scores, key=lambda x: (-x.count, x.player_score))


	def update_placements(self, scores: 'list[TeamPlayerScore]') -> 'list[TeamPlayerScore]':
		for i in range(len(scores)):
			if i > 0:
				if scores[i-1].count == scores[i].count \
					and scores[i-1].player_score == scores[i].player_score:
					scores[i].placement = scores[i-1].placement
				else:
					scores[i].placement = i+1
			else:
				scores[i].placement = i+1
		return scores


class ScoreTimeAttackPenaltyAuthorPlus15(ScoreTimeAttackDefault):
	"""
	Score sorting for TimeAttack where players who did not finish a map get a penalty time of Author + 15 seconds.
	Sorting: Summed finish time ascending
	"""

	def __init__(self) -> None:
		super().__init__()
		self.name = 'timeattack_penaltyauthorplus15'


	def combine_scores(self, scores: 'list[list[TeamPlayerScore]]', maps: 'list[MatchInfo]' = [], **kwargs) -> 'list[TeamPlayerScore]':
		all_players = {}	# type: dict[str, TeamPlayerScore]
		for map_scores in scores:
			for player_map_score in map_scores:
				if player_map_score.login not in all_players:
					all_players[player_map_score.login] = TeamPlayerScore(
						player_map_score.login,
						player_map_score.nickname,
						player_map_score.country,
						player_map_score.team_id,
						player_map_score.team_name,
						team_score=0,
						player_score=0,
						player_score2=0
					)
		combined_scores = list(all_players.values())	# type: list[TeamPlayerScore]
		for map_scores, map_info in zip(scores, maps):
			for combined_player_score in combined_scores:
				map_player_score = next((x for x in map_scores if x.login == combined_player_score.login), None)
				if map_player_score:
					combined_player_score.player_score += map_player_score.player_score
				else:
					combined_player_score.player_score += map_info.medal_author + 15000
		return combined_scores
