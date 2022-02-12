

class ResultsViewParams:
	map_name = ''
	map_start_time = 0
	mode_script = ''

	def __init__(self, map_name, map_start_time, mode_script) -> None:
		self.map_name = map_name
		self.map_start_time = map_start_time
		self.mode_script = mode_script

	def __repr__(self) -> str:
		return f"<ResultsViewParams map_name:{self.map_name} map_start_time:{self.map_start_time} mode_script:{self.mode_script}>"


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

