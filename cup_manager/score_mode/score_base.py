import logging
from abc import ABC, abstractmethod

from ..app_types import TeamPlayerScore
from ..models import MatchInfo

from pyplanet.utils import times

logger = logging.getLogger(__name__)


class ScoreNames:
	def __init__(self, score1_name: str, score2_name: str, scoreteam_name: str) -> None:
		self.score1_name = score1_name
		self.score2_name = score2_name
		self.scoreteam_name = scoreteam_name


class ScoreModeBase(ABC):
	"""
	Score sorting abstract base class, provides no sorting functionality.
	Sorting: None
	"""

	def __init__(self) -> None:
		self.name = 'score_mode_base'
		self.display_name = 'Score-Mode Base (Abstract)'
		self.brief = '<Write short statement about sorting mode>'
		self.score1_is_time = False
		self.score2_is_time = False
		self.scoreteam_is_time = False
		self.use_score1 = False
		self.use_score2 = False
		self.use_scoreteam = False
		self.score_names = ScoreNames(score1_name='Score', score2_name='Score', scoreteam_name='Team Score')


	@abstractmethod
	def combine_scores(self, scores: 'list[list[TeamPlayerScore]]', maps: 'list[MatchInfo]'=[], **kwargs) -> 'list[TeamPlayerScore]':
		pass


	@abstractmethod
	def sort_scores(self, scores: 'list[TeamPlayerScore]') -> 'list[TeamPlayerScore]':
		pass


	@abstractmethod
	def update_placements(self, scores: 'list[TeamPlayerScore]') -> 'list[TeamPlayerScore]':
		pass


	def get_ties(self, scores: 'list[TeamPlayerScore]') -> 'dict[str, list[TeamPlayerScore]]':
		ties_by_login = {}	# type: dict[str, list[TeamPlayerScore]]
		for score in scores:
			tied_scores = [s for s in scores if s.placement == score.placement and s.login != score.login]
			if len(tied_scores) > 0:
				ties_by_login[score.login] = tied_scores
		return ties_by_login


	def update_score_is_time(self, scores: 'list[TeamPlayerScore]') -> 'list[TeamPlayerScore]':
		for score in scores:
			score.player_score_is_time = self.score1_is_time
			score.player_score2_is_time = self.score2_is_time
			score.team_score_is_time = self.scoreteam_is_time
		return scores


	def score1_relevant(self) -> bool:
		return self.use_score1


	def score2_relevant(self) -> bool:
		return self.use_score2


	def scoreteam_relevant(self) -> bool:
		return self.use_scoreteam


	def get_score_names(self) -> ScoreNames:
		return self.score_names


	def relevant_score_str(self, score: TeamPlayerScore, maniascript_format: str=None) -> str:
		score_items = []	# type: list[str]
		if self.use_scoreteam:
			score_items.append(str(score.team_score_str))
		if self.use_score2:
			score_items.append(str(score.player_score2_str))
		if self.use_score1:
			score_items.append(str(score.player_score_str))
		score_str = ''	# type: str
		if maniascript_format:
			score_str = ','.join([f"$<{maniascript_format}{score_item}$>" for score_item in score_items])
		else:
			score_str = ','.join(score_items)
		return score_str


	def diff_scores_str(self, score: TeamPlayerScore, other: TeamPlayerScore) -> str:
		diff_items = []	# type: list[str]
		if self.use_scoreteam:
			teamscore_diff = abs(other.team_score - score.team_score)
			diff_items.append(times.format_time(teamscore_diff) if score.team_score_is_time else str(teamscore_diff))
		if self.use_score2:
			score2_diff = abs(other.player_score2 - score.player_score2)
			diff_items.append(times.format_time(score2_diff) if score.player_score2_is_time else str(score2_diff))
		if self.use_score1:
			score1_diff = abs(other.player_score - score.player_score)
			diff_items.append(times.format_time(score1_diff) if score.player_score_is_time else str(score1_diff))
		return ', '.join(diff_items)
