from enum import Enum
import logging

from pyplanet.utils import times

from .models import PlayerScore

logger = logging.getLogger(__name__)

class ScoreSortingPresets(Enum):
	UNDEFINED = -1
	TIMEATTACK = 0
	LAPS = 1
	ROUNDS = 2


	@staticmethod
	def get_preset(mode: str) -> 'ScoreSortingPresets':
		mode_lower = mode.lower()
		if 'timeattack' in mode_lower:
			preset = ScoreSortingPresets.TIMEATTACK
		elif 'laps' in mode_lower:
			preset = ScoreSortingPresets.LAPS
		elif 'rounds' in mode_lower:
			preset = ScoreSortingPresets.ROUNDS
		else:
			preset = ScoreSortingPresets.UNDEFINED
		return preset


class GenericPlayerScore:
	login = ''
	nickname = ''
	country = ''
	score = 0
	score2 = 0
	team = 0


	def __init__(self, login, nickname, country, score, score2=0, team=0) -> None:
		self.login = login
		self.nickname = nickname
		self.country = country
		self.score = score
		self.score2 = score2
		self.team = team


	def __repr__(self) -> str:
		return f"<GenericPlayerScore login:{self.login} nickname:{self.nickname} country:{self.country} score:{self.score} score2:{self.score2} team:{self.team}>"


class GenericTeamScore:
	id = 0
	name = ''
	score = 0


	def __init__(self, id, name, score) -> None:
		self.id = id
		self.name = name
		self.score = score


	def __repr__(self) -> str:
		return f"<GenericTeamScore id:{self.id} name:{self.name} score:{self.score}>"


class TeamPlayerScore:
	login = ''
	nickname = ''
	country = ''
	team_id = 0
	team_name = ''
	team_score = 0
	player_score = 0
	player_score2 = 0
	team_score_is_time = False
	player_score_is_time = False
	player_score2_is_time = False
	count = 1
	placement = 0


	def __init__(self, login, nickname, country, team_id, team_name, team_score, player_score, player_score2) -> None:
		self.login = login
		self.nickname = nickname
		self.country = country
		self.team_id = team_id
		self.team_name = team_name
		self.team_score = team_score
		self.player_score = player_score
		self.player_score2 = player_score2


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
	score = None
	payment = 0


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
