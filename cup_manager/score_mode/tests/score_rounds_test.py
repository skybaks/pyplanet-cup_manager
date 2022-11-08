import unittest
from copy import deepcopy

from ...app_types import TeamPlayerScore
from ..score_rounds import ScoreRoundsDefault


def create_results_rounds() -> 'list[TeamPlayerScore]':
	results = [
		TeamPlayerScore('p01', 'player 01', 'France', -1, '', 0, 121, 0),
		TeamPlayerScore('p02', 'player 02', 'France', -1, '', 0, 150, 0),	# tie
		TeamPlayerScore('p03', 'player 03', 'France', -1, '', 0, 149, 0),
		TeamPlayerScore('p04', 'player 04', 'France', -1, '', 0, 134, 0),
		TeamPlayerScore('p05', 'player 05', 'France', -1, '', 0, 267, 0),
		TeamPlayerScore('p06', 'player 06', 'France', -1, '', 0, 201, 0),
		TeamPlayerScore('p07', 'player 07', 'France', -1, '', 0, 150, 0),	# tie
	]
	return results


def create_results_rounds2() -> 'list[TeamPlayerScore]':
	results = [
		TeamPlayerScore('p01', 'player 01', 'France', -1, '', 0, 130, 0),
		TeamPlayerScore('p02', 'player 02', 'France', -1, '', 0, 140, 0),
		TeamPlayerScore('p03', 'player 03', 'France', -1, '', 0, 170, 0),
		TeamPlayerScore('p04', 'player 04', 'France', -1, '', 0, 160, 0),
		TeamPlayerScore('p05', 'player 05', 'France', -1, '', 0, 123, 0),
		TeamPlayerScore('p06', 'player 06', 'France', -1, '', 0, 104, 0),
		TeamPlayerScore('p07', 'player 07', 'France', -1, '', 0, 129, 0),
	]
	return results


def create_results_rounds3() -> 'list[TeamPlayerScore]':
	results = [
		TeamPlayerScore('p02', 'player 02', 'France', -1, '', 0, 140, 0),
		TeamPlayerScore('p03', 'player 03', 'France', -1, '', 0, 170, 0),
		TeamPlayerScore('p04', 'player 04', 'France', -1, '', 0, 160, 0),
		TeamPlayerScore('p05', 'player 05', 'France', -1, '', 0, 123, 0),
		TeamPlayerScore('p06', 'player 06', 'France', -1, '', 0, 104, 0),
		TeamPlayerScore('p07', 'player 07', 'France', -1, '', 0, 129, 0),
		TeamPlayerScore('p08', 'player 08', 'France', -1, '', 0, 101, 0),
	]
	return results


class ScoreRoundsDefaultTest(unittest.TestCase):


	def test_sort_scores(self):
		results = create_results_rounds()
		results_copy = deepcopy(results)
		sorting = ScoreRoundsDefault()
		results = sorting.sort_scores(results)
		self.assertNotEqual(results, results_copy)
		self.assertEqual(7, len(results))
		self.assertEqual('p05', results[0].login)
		self.assertEqual('p06', results[1].login)
		self.assertEqual('p02', results[2].login)
		self.assertEqual('p07', results[3].login)
		self.assertEqual('p03', results[4].login)
		self.assertEqual('p04', results[5].login)
		self.assertEqual('p01', results[6].login)


	def test_combine_scores(self):
		results = create_results_rounds()
		results_copy = deepcopy(results)
		sorting = ScoreRoundsDefault()
		results = sorting.combine_scores(results, create_results_rounds2())
		results = sorting.combine_scores(results, create_results_rounds3())
		self.assertNotEqual(results, results_copy)
		self.assertEqual(8, len(results))
		self.assertEqual('p01', results[0].login)
		self.assertEqual('p02', results[1].login)
		self.assertEqual('p03', results[2].login)
		self.assertEqual('p04', results[3].login)
		self.assertEqual('p05', results[4].login)
		self.assertEqual('p06', results[5].login)
		self.assertEqual('p07', results[6].login)
		self.assertEqual('p08', results[7].login)
		self.assertEqual(121+130+0, results[0].player_score)
		self.assertEqual(150+140+140, results[1].player_score)
		self.assertEqual(149+170+170, results[2].player_score)
		self.assertEqual(134+160+160, results[3].player_score)
		self.assertEqual(267+123+123, results[4].player_score)
		self.assertEqual(201+104+104, results[5].player_score)
		self.assertEqual(150+129+129, results[6].player_score)
		self.assertEqual(0+0+101, results[7].player_score)


	def test_update_placements(self):
		results = create_results_rounds()
		sorting = ScoreRoundsDefault()
		results = sorting.sort_scores(results)
		results_copy = deepcopy(results)
		results = sorting.update_placements(results)
		self.assertNotEqual(results, results_copy)
		self.assertEqual(7, len(results))
		self.assertEqual(1, results[0].placement)
		self.assertEqual(2, results[1].placement)
		self.assertEqual(3, results[2].placement)
		self.assertEqual(3, results[3].placement)
		self.assertEqual(results[2].player_score, results[3].player_score)
		self.assertEqual(5, results[4].placement)
		self.assertEqual(6, results[5].placement)
		self.assertEqual(7, results[6].placement)


	def test_get_ties(self):
		results = create_results_rounds()
		sorting = ScoreRoundsDefault()
		results = sorting.sort_scores(results)
		results = sorting.update_placements(results)
		ties = sorting.get_ties(results)
		self.assertEqual(2, len(ties))
		self.assertTrue('p02' in ties)
		self.assertEqual(1, len(ties['p02']))
		self.assertEqual('p07', ties['p02'][0].login)
		self.assertTrue('p07' in ties)
		self.assertEqual(1, len(ties['p07']))
		self.assertEqual('p02', ties['p07'][0].login)


	def test_update_score_is_time(self):
		results = create_results_rounds()
		sorting = ScoreRoundsDefault()
		results = sorting.update_score_is_time(results)
		for result in results:
			self.assertFalse(result.player_score_is_time)
			self.assertFalse(result.player_score2_is_time)
			self.assertFalse(result.team_score_is_time)


	def test_score1_relevant(self):
		sorting = ScoreRoundsDefault()
		self.assertTrue(sorting.score1_relevant())


	def test_score2_relevant(self):
		sorting = ScoreRoundsDefault()
		self.assertFalse(sorting.score2_relevant())


	def test_scoreteam_relevant(self):
		sorting = ScoreRoundsDefault()
		self.assertFalse(sorting.scoreteam_relevant())


	def test_relevant_score_str(self):
		sorting = ScoreRoundsDefault()
		score = TeamPlayerScore('p01', 'player 01', 'France', -1, '', 0, 130, 0)
		result_str = sorting.relevant_score_str(score)
		self.assertEqual('130', result_str)
		result_str = sorting.relevant_score_str(score, '$fff')
		self.assertEqual('$<$fff130$>', result_str)


	def test_diff_scores_str(self):
		sorting = ScoreRoundsDefault()
		score1 = TeamPlayerScore('p01', 'player 01', 'France', -1, '', 0, 121, 0)
		score2 = TeamPlayerScore('p02', 'player 02', 'France', -1, '', 0, 150, 0)
		diff_str = sorting.diff_scores_str(score1, score2)
		self.assertEqual('29', diff_str)


if __name__ == '__main__':
	unittest.main()
