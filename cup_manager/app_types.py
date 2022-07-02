from enum import Enum
from pyplanet.utils import times


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


	@property
	def team_score_str(self) -> str:
		return times.format_time(int(self.team_score)) if self.team_score_is_time else str(self.team_score)


	@property
	def player_score_str(self) -> str:
		return times.format_time(int(self.player_score)) if self.player_score_is_time else str(self.player_score)


	@property
	def player_score2_str(self) -> str:
		return times.format_time(int(self.player_score2)) if self.player_score2_is_time else str(self.player_score2)


	def relevant_score_str(self, sorting: ScoreSortingPresets) -> str:
		score_str = ''
		if sorting == ScoreSortingPresets.TIMEATTACK:
			score_str = str(self.player_score_str)
		elif sorting == ScoreSortingPresets.LAPS:
			score_str = str(self.player_score2_str) + ', ' + str(self.player_score_str)
		elif sorting == ScoreSortingPresets.ROUNDS:
			score_str = str(self.player_score_str)
		else:
			score_str = str(self.team_score) + ', ' + str(self.player_score_str)
		return score_str


	@staticmethod
	def sort_scores(input_scores: 'list[TeamPlayerScore]', sorting: ScoreSortingPresets=ScoreSortingPresets.UNDEFINED) -> 'list[TeamPlayerScore]':
		if sorting == ScoreSortingPresets.TIMEATTACK:
			# 1.	maps	desc	(maps played)
			# 2.	score	asc		(finish time)
			sort_method = lambda x: (-x.count, x.player_score)
		elif sorting == ScoreSortingPresets.LAPS:
			# 1.	score2	desc	(checkpoint count)
			# 2.	score	asc		(finish time)
			sort_method = lambda x: (-x.player_score2, x.player_score)
		elif sorting == ScoreSortingPresets.ROUNDS:
			# 1.	score	desc	(player score)
			sort_method = lambda x: (-x.player_score)
		else:
			# 1.	team	desc	(team score)
			# 3.	score	desc	(score)
			sort_method = lambda x: (-x.team_score, -x.player_score)
		return sorted(input_scores, key=sort_method)


	@staticmethod
	def diff_scores_str(score: 'TeamPlayerScore', other: 'TeamPlayerScore', sorting: ScoreSortingPresets) -> str:
		diff_str = ''

		count_diff = abs(other.count - score.count)
		score1_diff = abs(other.player_score - score.player_score)
		score2_diff = abs(other.player_score2 - score.player_score2)
		team_score_diff = abs(other.team_score - score.team_score)

		if sorting == ScoreSortingPresets.TIMEATTACK:
			diff_str = times.format_time(score1_diff)
		elif sorting == ScoreSortingPresets.LAPS:
			diff_str = str(score2_diff) + ' CP(s), ' + times.format_time(score1_diff)
		elif sorting == ScoreSortingPresets.ROUNDS:
			diff_str = str(score1_diff) + ' point(s)'
		else:
			diff_str = str(team_score_diff) + ' team point(s), ' + str(score1_diff) + ' point(s)'
		return diff_str


	@staticmethod
	def update_placements(input_scores: 'list[TeamPlayerScore]', sorting: ScoreSortingPresets=ScoreSortingPresets.UNDEFINED) -> 'list[TeamPlayerScore]':
		for index in range(0, len(input_scores)):
			if index > 0:

				if sorting == ScoreSortingPresets.TIMEATTACK:
					if input_scores[index-1].count == input_scores[index].count \
							and input_scores[index-1].player_score == input_scores[index].player_score:
						input_scores[index].placement = input_scores[index-1].placement
					else:
						input_scores[index].placement = index + 1

				elif sorting == ScoreSortingPresets.LAPS:
					if input_scores[index-1].player_score2 == input_scores[index].player_score2 \
							and input_scores[index-1].player_score == input_scores[index].player_score:
						input_scores[index].placement = input_scores[index-1].placement
					else:
						input_scores[index].placement = index + 1

				elif sorting == ScoreSortingPresets.ROUNDS:
					if input_scores[index-1].player_score == input_scores[index].player_score:
						input_scores[index].placement = input_scores[index-1].placement
					else:
						input_scores[index].placement = index + 1

				else:
					if input_scores[index-1].team_score == input_scores[index].team_score \
							and input_scores[index-1].player_score == input_scores[index].player_score:
						input_scores[index].placement = input_scores[index-1].placement
					else:
						input_scores[index].placement = index + 1
			else:
				input_scores[index].placement = 1
		return input_scores
