
from pyplanet.utils import times


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


	@property
	def team_score_str(self) -> str:
		return times.format_time(int(self.team_score)) if self.team_score_is_time else str(self.team_score)


	@property
	def player_score_str(self) -> str:
		return times.format_time(int(self.player_score)) if self.player_score_is_time else str(self.player_score)


	@property
	def player_score2_str(self) -> str:
		return times.format_time(int(self.player_score2)) if self.player_score2_is_time else str(self.player_score2)
