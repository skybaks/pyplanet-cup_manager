import unittest
from copy import deepcopy

from ...app_types import TeamPlayerScore
from ...models import MatchInfo
from ..score_base import ScoreModeBase


def create_results() -> 'list[TeamPlayerScore]':
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


def create_results2() -> 'list[TeamPlayerScore]':
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


def create_results3() -> 'list[TeamPlayerScore]':
	return [
		TeamPlayerScore('p01', 'player 01', 'France', 1, 'Red', 3, 26, 0),
		TeamPlayerScore('p02', 'player 02', 'France', 1, 'Red', 3, 19, 0),
		TeamPlayerScore('p03', 'player 03', 'France', 2, 'Blu', 4, 19, 0),
		TeamPlayerScore('p04', 'player 04', 'France', 2, 'Blu', 4, 21, 0),
		TeamPlayerScore('p05', 'player 05', 'France', 1, 'Red', 3, 19, 0),
	]


class ScoreModeBaseImpl(ScoreModeBase):
	def combine_scores(self, scores: 'list[list[TeamPlayerScore]]', maps: 'list[MatchInfo]'=[], **kwargs) -> 'list[TeamPlayerScore]':
		return []

	def sort_scores(self, scores: 'list[TeamPlayerScore]') -> 'list[TeamPlayerScore]':
		return []

	def update_placements(self, scores: 'list[TeamPlayerScore]') -> 'list[TeamPlayerScore]':
		return []


class ScoreModeBaseTest(unittest.TestCase):


	def test_sort_scores(self):
		results = create_results()
		results_copy = deepcopy(results)
		sorting = ScoreModeBaseImpl()
		results = sorting.sort_scores(results)
		self.assertNotEqual(results, results_copy)


	def test_combine_scores(self):
		results = create_results()
		results2 = create_results2()
		results_copy = deepcopy(results)
		sorting = ScoreModeBaseImpl()
		results = sorting.combine_scores([results, results2])
		self.assertNotEqual(results, results_copy)


	def test_update_placements(self):
		results = create_results()
		results_copy = deepcopy(results)
		sorting = ScoreModeBaseImpl()
		results = sorting.update_placements(results)
		self.assertNotEqual(results, results_copy)


	def test_get_ties(self):
		results = create_results()
		sorting = ScoreModeBaseImpl()
		results[0].placement = 1	# tie#1
		results[1].placement = 1	# tie#1
		results[2].placement = 3
		results[3].placement = 4	# tie#2
		results[4].placement = 4	# tie#2
		results[5].placement = 4	# tie#2
		results[6].placement = 7
		ties = sorting.get_ties(results)
		self.assertEqual(5, len(ties.keys()))
		self.assertTrue('p01' in ties)
		self.assertTrue('p02' in ties)
		self.assertFalse('p03' in ties)
		self.assertTrue('p04' in ties)
		self.assertTrue('p05' in ties)
		self.assertTrue('p06' in ties)
		self.assertFalse('p07' in ties)
		self.assertEqual(1, len(ties['p01']))
		self.assertEqual(1, len(ties['p02']))
		self.assertEqual(2, len(ties['p04']))
		self.assertEqual(2, len(ties['p05']))
		self.assertEqual(2, len(ties['p06']))


	def test_update_score_is_time(self):
		results = create_results()
		sorting = ScoreModeBaseImpl()
		results = sorting.update_score_is_time(results)
		for result in results:
			self.assertFalse(result.player_score_is_time)
			self.assertFalse(result.player_score2_is_time)
			self.assertFalse(result.team_score_is_time)


	def test_score1_relevant(self):
		sorting = ScoreModeBaseImpl()
		self.assertFalse(sorting.score1_relevant())


	def test_score2_relevant(self):
		sorting = ScoreModeBaseImpl()
		self.assertFalse(sorting.score2_relevant())


	def test_scoreteam_relevant(self):
		sorting = ScoreModeBaseImpl()
		self.assertFalse(sorting.scoreteam_relevant())


	def test_get_score_names(self):
		sorting = ScoreModeBaseImpl()
		names = sorting.get_score_names()
		self.assertEqual('Score', names.score1_name)
		self.assertEqual('Score', names.score2_name)
		self.assertEqual('Team Score', names.scoreteam_name)


	def test_relevant_score_str(self):
		sorting = ScoreModeBaseImpl()
		score = TeamPlayerScore('login', 'name', 'Any', -1, '', 0, 124, 0)
		score_str = sorting.relevant_score_str(score)
		self.assertEqual('', score_str)
		score_str = sorting.relevant_score_str(score, '$fff')
		self.assertEqual('', score_str)


	def test_diff_scores_str(self):
		sorting = ScoreModeBaseImpl()
		score1 = TeamPlayerScore('login1', 'name1', 'Any', -1, '', 0, 124, 0)
		score2 = TeamPlayerScore('login2', 'name2', 'Any', -1, '', 0, 103, 0)
		diff_str = sorting.diff_scores_str(score1, score2)
		self.assertEqual('', diff_str)


if __name__ == '__main__':
	unittest.main()
