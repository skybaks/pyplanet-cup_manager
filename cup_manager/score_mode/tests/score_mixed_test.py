import unittest

from ...app_types import TeamPlayerScore
from ...models import MatchInfo
from ..score_mixed import ScoreModeMixed


def create_results_rounds() -> 'list[TeamPlayerScore]':
	return [
		TeamPlayerScore('p01', 'player 01', 'France', -1, '', 0, 121, 0),
		TeamPlayerScore('p02', 'player 02', 'France', -1, '', 0, 150, 0),	# tie
		TeamPlayerScore('p03', 'player 03', 'France', -1, '', 0, 149, 0),
		TeamPlayerScore('p04', 'player 04', 'France', -1, '', 0, 134, 0),
		TeamPlayerScore('p05', 'player 05', 'France', -1, '', 0, 267, 0),
		TeamPlayerScore('p06', 'player 06', 'France', -1, '', 0, 201, 0),
		TeamPlayerScore('p07', 'player 07', 'France', -1, '', 0, 150, 0),	# tie
	]


def create_results_ta() -> 'list[TeamPlayerScore]':
	return [
		TeamPlayerScore('p01', 'name01', 'Any', -1, '', 0, 49502, 0),
		TeamPlayerScore('p02', 'name02', 'Any', -1, '', 0, 47215, 0),
		TeamPlayerScore('p03', 'name03', 'Any', -1, '', 0, 49897, 0),
		TeamPlayerScore('p04', 'name04', 'Any', -1, '', 0, 48163, 0),
		TeamPlayerScore('p05', 'name05', 'Any', -1, '', 0, 47641, 0),
	]


def create_results_laps() -> 'list[TeamPlayerScore]':
	return [
		TeamPlayerScore('p01', 'name01', 'Any', -1, '', 0, 76647, 120),
		TeamPlayerScore('p02', 'name02', 'Any', -1, '', 0, 82749, 120),
		TeamPlayerScore('p03', 'name03', 'Any', -1, '', 0, 79546, 120),
		TeamPlayerScore('p04', 'name04', 'Any', -1, '', 0, 29648, 32),
		TeamPlayerScore('p05', 'name05', 'Any', -1, '', 0, 59497, 70),
	]


class ScoreModeMixedTest(unittest.TestCase):


	def test_combine_scores(self):
		sorting = ScoreModeMixed()
		results = sorting.combine_scores([create_results_rounds()], [MatchInfo(mode_script='rounds')])
		self.assertEqual(7, len(results))
		self.assertEqual('p05', results[0].login)
		self.assertEqual('p06', results[1].login)
		self.assertEqual('p02', results[2].login)
		self.assertEqual('p07', results[3].login)
		self.assertEqual('p03', results[4].login)
		self.assertEqual('p04', results[5].login)
		self.assertEqual('p01', results[6].login)
		self.assertEqual(7, results[0].player_score)
		self.assertEqual(6, results[1].player_score)
		self.assertEqual(5, results[2].player_score)
		self.assertEqual(5, results[3].player_score)
		self.assertEqual(3, results[4].player_score)
		self.assertEqual(2, results[5].player_score)
		self.assertEqual(1, results[6].player_score)


	def test_combine_scores2(self):
		sorting = ScoreModeMixed()
		results = sorting.combine_scores(
			[create_results_rounds(), create_results_ta(), create_results_laps()],
			[MatchInfo(mode_script='rounds'), MatchInfo(mode_script='timeattack'), MatchInfo(mode_script='laps')]
		)
		self.assertEqual(7, len(results))
		self.assertEqual('p05', results[0].login)
		self.assertEqual('p06', results[1].login)
		self.assertEqual('p02', results[2].login)
		self.assertEqual('p07', results[3].login)
		self.assertEqual('p03', results[4].login)
		self.assertEqual('p04', results[5].login)
		self.assertEqual('p01', results[6].login)
		self.assertEqual(7+4+2, results[0].player_score)
		self.assertEqual(6+0+0, results[1].player_score)
		self.assertEqual(5+5+3, results[2].player_score)
		self.assertEqual(5+0+0, results[3].player_score)
		self.assertEqual(3+1+4, results[4].player_score)
		self.assertEqual(2+3+1, results[5].player_score)
		self.assertEqual(1+2+5, results[6].player_score)


	def test_sort_scores(self):
		sorting = ScoreModeMixed()
		results = sorting.combine_scores(
			[create_results_rounds(), create_results_ta(), create_results_laps()],
			[MatchInfo(mode_script='rounds'), MatchInfo(mode_script='timeattack'), MatchInfo(mode_script='laps')]
		)
		results = sorting.sort_scores(results)
		self.assertEqual(7, len(results))
		self.assertEqual('p05', results[0].login)
		self.assertEqual('p02', results[1].login)
		self.assertEqual('p03', results[2].login)
		self.assertEqual('p01', results[3].login)
		self.assertEqual('p06', results[4].login)
		self.assertEqual('p04', results[5].login)
		self.assertEqual('p07', results[6].login)
		self.assertEqual(7+4+2, results[0].player_score)
		self.assertEqual(5+5+3, results[1].player_score)
		self.assertEqual(3+1+4, results[2].player_score)
		self.assertEqual(1+2+5, results[3].player_score)
		self.assertEqual(6+0+0, results[4].player_score)
		self.assertEqual(2+3+1, results[5].player_score)
		self.assertEqual(5+0+0, results[6].player_score)


	def test_update_placements(self):
		sorting = ScoreModeMixed()
		results = sorting.combine_scores(
			[create_results_rounds(), create_results_ta(), create_results_laps()],
			[MatchInfo(mode_script='rounds'), MatchInfo(mode_script='timeattack'), MatchInfo(mode_script='laps')]
		)
		results = sorting.sort_scores(results)
		results = sorting.update_placements(results)
		self.assertEqual(7, len(results))
		self.assertEqual(1, results[0].placement)
		self.assertEqual(1, results[1].placement)
		self.assertEqual(results[0].player_score, results[1].player_score)
		self.assertEqual(3, results[2].placement)
		self.assertEqual(3, results[3].placement)
		self.assertEqual(results[2].player_score, results[3].player_score)
		self.assertEqual(5, results[4].placement)
		self.assertEqual(5, results[5].placement)
		self.assertEqual(7, results[6].placement)


	def test_get_ties(self):
		sorting = ScoreModeMixed()
		results = sorting.combine_scores(
			[create_results_rounds(), create_results_ta(), create_results_laps()],
			[MatchInfo(mode_script='rounds'), MatchInfo(mode_script='timeattack'), MatchInfo(mode_script='laps')]
		)
		results = sorting.sort_scores(results)
		results = sorting.update_placements(results)
		ties = sorting.get_ties(results)
		self.assertEqual(6, len(ties))


	def test_update_score_is_time(self):
		results = create_results_rounds()
		sorting = ScoreModeMixed()
		results = sorting.update_score_is_time(results)
		for result in results:
			self.assertFalse(result.player_score_is_time)
			self.assertFalse(result.player_score2_is_time)
			self.assertFalse(result.team_score_is_time)


	def test_score1_relevant(self):
		sorting = ScoreModeMixed()
		self.assertTrue(sorting.score1_relevant())


	def test_score2_relevant(self):
		sorting = ScoreModeMixed()
		self.assertFalse(sorting.score2_relevant())


	def test_scoreteam_relevant(self):
		sorting = ScoreModeMixed()
		self.assertFalse(sorting.scoreteam_relevant())


	def test_relevant_score_str(self):
		sorting = ScoreModeMixed()
		score = TeamPlayerScore('p01', 'player 01', 'France', -1, '', 0, 130, 0)
		result_str = sorting.relevant_score_str(score)
		self.assertEqual('130', result_str)
		result_str = sorting.relevant_score_str(score, '$fff')
		self.assertEqual('$<$fff130$>', result_str)


	def test_diff_scores_str(self):
		sorting = ScoreModeMixed()
		score1 = TeamPlayerScore('p01', 'player 01', 'France', -1, '', 0, 121, 0)
		score2 = TeamPlayerScore('p02', 'player 02', 'France', -1, '', 0, 150, 0)
		diff_str = sorting.diff_scores_str(score1, score2)
		self.assertEqual('29', diff_str)


if __name__ == '__main__':
	unittest.main()
