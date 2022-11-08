import unittest
from copy import deepcopy

from ...app_types import TeamPlayerScore
from ..score_laps import ScoreLapsDefault

def create_results_laps1() -> 'list[TeamPlayerScore]':
	return [
		TeamPlayerScore('p01', 'name01', 'Any', -1, '', 0, 76647, 120),
		TeamPlayerScore('p02', 'name02', 'Any', -1, '', 0, 82749, 120),
		TeamPlayerScore('p03', 'name03', 'Any', -1, '', 0, 79546, 120),
		TeamPlayerScore('p04', 'name04', 'Any', -1, '', 0, 29648, 32),
		TeamPlayerScore('p05', 'name05', 'Any', -1, '', 0, 59497, 70),
	]

def create_results_laps2() -> 'list[TeamPlayerScore]':
	return [
		TeamPlayerScore('p01', 'name01', 'Any', -1, '', 0, 96675, 90),
		TeamPlayerScore('p02', 'name02', 'Any', -1, '', 0, 96675, 90),
		TeamPlayerScore('p03', 'name03', 'Any', -1, '', 0, 92482, 90),
		TeamPlayerScore('p04', 'name04', 'Any', -1, '', 0, 81693, 65),
	]


class ScoreLapsDefaultTest(unittest.TestCase):


	def test_combine_scores(self):
		results = create_results_laps1()
		results_copy = deepcopy(results)
		sorting = ScoreLapsDefault()
		results = sorting.combine_scores([results, create_results_laps2()])
		self.assertNotEqual(results, results_copy)
		self.assertEqual(5, len(results))


	def test_sort_scores(self):
		results = create_results_laps1()
		results_copy = deepcopy(results)
		sorting = ScoreLapsDefault()
		results = sorting.sort_scores(results)
		self.assertNotEqual(results, results_copy)
		self.assertEqual('p01', results[0].login)
		self.assertEqual('p03', results[1].login)
		self.assertEqual('p02', results[2].login)
		self.assertEqual('p05', results[3].login)
		self.assertEqual('p04', results[4].login)


	def test_update_placement(self):
		sorting = ScoreLapsDefault()
		results = sorting.sort_scores(create_results_laps2())
		results_copy = deepcopy(results)
		results = sorting.update_placements(results)
		self.assertNotEqual(results, results_copy)
		self.assertEqual(1, results[0].placement)
		self.assertEqual(2, results[1].placement)
		self.assertEqual(2, results[2].placement)
		self.assertEqual(4, results[3].placement)


	def test_get_ties(self):
		sorting = ScoreLapsDefault()
		results = sorting.sort_scores(create_results_laps2())
		results = sorting.update_placements(results)
		ties = sorting.get_ties(results)
		self.assertEqual(2, len(ties))
		self.assertTrue('p01' in ties)
		self.assertEqual(1, len(ties['p01']))
		self.assertEqual('p02', ties['p01'][0].login)
		self.assertTrue('p02' in ties)
		self.assertEqual(1, len(ties['p02']))
		self.assertEqual('p01', ties['p02'][0].login)


	def test_update_score_is_time(self):
		sorting = ScoreLapsDefault()
		results = sorting.update_score_is_time(create_results_laps1())
		for result in results:
			self.assertTrue(result.player_score_is_time)
			self.assertFalse(result.player_score2_is_time)
			self.assertFalse(result.team_score_is_time)


	def test_score1_relevant(self):
		sorting = ScoreLapsDefault()
		self.assertTrue(sorting.score1_relevant())


	def test_score2_relevant(self):
		sorting = ScoreLapsDefault()
		self.assertTrue(sorting.score2_relevant())


	def test_scoreteam_relevant(self):
		sorting = ScoreLapsDefault()
		self.assertFalse(sorting.scoreteam_relevant())


	def test_relevant_score_str(self):
		sorting = ScoreLapsDefault()
		score = TeamPlayerScore('p01', 'name01', 'Any', -1, '', 0, 67418, 150)
		results = sorting.update_score_is_time([score])
		result_str = sorting.relevant_score_str(results[0])
		self.assertEqual('150,1:07.418', result_str)
		result_str = sorting.relevant_score_str(results[0], '$fff')
		self.assertEqual('$<$fff150$>,$<$fff1:07.418$>', result_str)


	def test_diff_scores_str(self):
		sorting = ScoreLapsDefault()
		score1 = TeamPlayerScore('p01', 'name01', 'Any', -1, '', 0, 67418, 150)
		score2 = TeamPlayerScore('p02', 'name02', 'Any', -1, '', 0, 65273, 149)
		results = sorting.update_score_is_time([score1, score2])
		results_str = sorting.diff_scores_str(results[0], results[1])
		self.assertEqual('1, 0:02.145', results_str)


if __name__ == '__main__':
	unittest.main()
