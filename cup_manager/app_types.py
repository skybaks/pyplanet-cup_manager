from enum import Enum
import logging

from pyplanet.utils import times

from .models import PlayerScore

logger = logging.getLogger(__name__)


class GenericPlayerScore:
	def __init__(self) -> None:
		self.login = ''
		self.nickname = ''
		self.country = ''
		self.score = 0
		self.score2 = 0
		self.team = -1
		self.score_match = 0

	def __repr__(self) -> str:
		return f"<GenericPlayerScore login:{self.login} nickname:{self.nickname} country:{self.country} score:{self.score} score2:{self.score2} team:{self.team} score_match:{self.score_match}>"


class GenericTeamScore:
	def __init__(self, team_id, name, score) -> None:
		self.id = team_id
		self.name = name
		self.score = score

	def __repr__(self) -> str:
		return f"<GenericTeamScore id:{self.id} name:{self.name} score:{self.score}>"


class TeamPlayerScore:
	def __init__(self, login, nickname, country, team_id, team_name, team_score, player_score, player_score2) -> None:
		self.login = login
		self.nickname = nickname
		self.country = country
		self.team_id = team_id
		self.team_name = team_name
		self.team_score = team_score
		self.player_score = player_score
		self.player_score2 = player_score2
		self.team_score_is_time = False
		self.player_score_is_time = False
		self.player_score2_is_time = False
		self.count = 1
		self.placement = 0


	def __repr__(self) -> str:
		return f"<TeamPlayerScore login:{self.login} nickname:{self.nickname} country:{self.country} team_id:{self.team_id} team_name:{self.team_name} team_score:{self.team_score_str} player_score:{self.player_score_str} player_score2:{self.player_score2_str}>"


	def __eq__(self, __o: 'TeamPlayerScore') -> bool:
		return self.login == __o.login \
			and self.nickname == __o.nickname \
			and self.country == __o.country \
			and self.team_id == __o.team_id \
			and self.team_name == __o.team_name \
			and self.team_score == __o.team_score \
			and self.player_score == __o.player_score \
			and self.player_score2 == __o.player_score2 \
			and self.team_score_is_time == __o.team_score_is_time \
			and self.player_score_is_time == __o.player_score_is_time \
			and self.player_score2_is_time == __o.player_score2_is_time \
			and self.count == __o.count \
			and self.placement == __o.placement


	@property
	def team_score_str(self) -> str:
		return times.format_time(int(self.team_score)) if self.team_score_is_time else str(self.team_score)


	@property
	def player_score_str(self) -> str:
		return times.format_time(int(self.player_score)) if self.player_score_is_time else str(self.player_score)


	@property
	def player_score2_str(self) -> str:
		return times.format_time(int(self.player_score2)) if self.player_score2_is_time else str(self.player_score2)


	@staticmethod
	def from_player_score(player_score: PlayerScore) -> 'TeamPlayerScore':
		return TeamPlayerScore(
			player_score.login,
			player_score.nickname,
			player_score.country,
			player_score.team,
			None,
			0,
			player_score.score,
			player_score.score2
		)


class PaymentScore:
	def __init__(self, score: TeamPlayerScore, payment: int) -> None:
		self.score = score
		self.payment = payment


	def __repr__(self) -> str:
		return f'<PaymentScore payment:{str(self.payment)} score:{str(self.score)}>'


	@property
	def amount(self) -> int:
		return self.payment


	@property
	def login(self) -> str:
		return self.score.login
