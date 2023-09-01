import unittest
from copy import deepcopy

from ...app_types import TeamPlayerScore
from ...models import MatchInfo
from ..score_timeattack import (
    ScoreTimeAttackDefault,
    ScoreTimeAttackPenaltyAuthorPlus15,
)


def create_results_ta1() -> "list[TeamPlayerScore]":
    return [
        TeamPlayerScore("p01", "name01", "Any", -1, "", 0, 49502, 0),
        TeamPlayerScore("p02", "name02", "Any", -1, "", 0, 47215, 0),
        TeamPlayerScore("p03", "name03", "Any", -1, "", 0, 49897, 0),
        TeamPlayerScore("p04", "name04", "Any", -1, "", 0, 48163, 0),
        TeamPlayerScore("p05", "name05", "Any", -1, "", 0, 47641, 0),
    ]


def create_results_ta2() -> "list[TeamPlayerScore]":
    return [
        TeamPlayerScore("p01", "name01", "Any", -1, "", 0, 25103, 0),
        TeamPlayerScore("p02", "name02", "Any", -1, "", 0, 24926, 0),
        TeamPlayerScore("p03", "name03", "Any", -1, "", 0, 26379, 0),
        TeamPlayerScore("p06", "name06", "Any", -1, "", 0, 47641, 0),
    ]


class ScoreTimeAttackDefaultTest(unittest.TestCase):
    def test_combine_scores(self):
        results = create_results_ta1()
        results_copy = deepcopy(results)
        sorting = ScoreTimeAttackDefault()
        results = sorting.combine_scores([results, create_results_ta2()])
        self.assertNotEqual(results, results_copy)
        self.assertEqual(6, len(results))

    def test_sort_scores(self):
        results = create_results_ta1()
        sorting = ScoreTimeAttackDefault()
        results = sorting.combine_scores([results, create_results_ta2()])
        results_copy = deepcopy(results)
        results = sorting.sort_scores(results)
        self.assertNotEqual(results, results_copy)
        self.assertEqual(6, len(results))
        self.assertEqual("p02", results[0].login)
        self.assertEqual("p01", results[1].login)
        self.assertEqual("p03", results[2].login)
        self.assertEqual("p05", results[3].login)
        self.assertEqual("p06", results[4].login)
        self.assertEqual("p04", results[5].login)
        self.assertEqual(47215 + 24926, results[0].player_score)
        self.assertEqual(49502 + 25103, results[1].player_score)
        self.assertEqual(49897 + 26379, results[2].player_score)
        self.assertEqual(0 + 47641, results[3].player_score)
        self.assertEqual(47641 + 0, results[4].player_score)
        self.assertEqual(48163 + 0, results[5].player_score)

    def test_update_placement(self):
        results = create_results_ta1()
        sorting = ScoreTimeAttackDefault()
        results = sorting.combine_scores([results, create_results_ta2()])
        results = sorting.sort_scores(results)
        results_copy = deepcopy(results)
        results = sorting.update_placements(results)
        self.assertNotEqual(results, results_copy)
        self.assertEqual(6, len(results))
        self.assertEqual(1, results[0].placement)
        self.assertEqual(2, results[1].placement)
        self.assertEqual(3, results[2].placement)
        self.assertEqual(4, results[3].placement)
        self.assertEqual(4, results[4].placement)
        self.assertEqual(6, results[5].placement)

    def test_get_ties(self):
        sorting = ScoreTimeAttackDefault()
        results = sorting.combine_scores([create_results_ta1(), create_results_ta2()])
        results = sorting.sort_scores(results)
        results = sorting.update_placements(results)
        ties = sorting.get_ties(results)
        self.assertEqual(2, len(ties))
        self.assertTrue("p05" in ties)
        self.assertEqual(1, len(ties["p05"]))
        self.assertEqual("p06", ties["p05"][0].login)
        self.assertTrue("p06" in ties)
        self.assertEqual(1, len(ties["p06"]))
        self.assertEqual("p05", ties["p06"][0].login)

    def test_update_score_is_time(self):
        results = create_results_ta1()
        sorting = ScoreTimeAttackDefault()
        results = sorting.update_score_is_time(results)
        for result in results:
            self.assertTrue(result.player_score_is_time)
            self.assertFalse(result.player_score2_is_time)
            self.assertFalse(result.team_score_is_time)

    def test_score1_relevant(self):
        sorting = ScoreTimeAttackDefault()
        self.assertTrue(sorting.score1_relevant())

    def test_score2_relevant(self):
        sorting = ScoreTimeAttackDefault()
        self.assertFalse(sorting.score2_relevant())

    def test_scoreteam_relevant(self):
        sorting = ScoreTimeAttackDefault()
        self.assertFalse(sorting.scoreteam_relevant())

    def test_relevant_score_str(self):
        sorting = ScoreTimeAttackDefault()
        score = TeamPlayerScore("p01", "name01", "Any", -1, "", 0, 49502, 0)
        results = sorting.update_score_is_time([score])
        result_str = sorting.relevant_score_str(results[0])
        self.assertEqual("0:49.502", result_str)
        result_str = sorting.relevant_score_str(results[0], "$fff")
        self.assertEqual("$<$fff0:49.502$>", result_str)

    def test_diff_scores_str(self):
        sorting = ScoreTimeAttackDefault()
        results = create_results_ta1()
        results = sorting.update_score_is_time(results)
        results_str = sorting.diff_scores_str(results[0], results[1])
        self.assertEqual("0:02.287", results_str)


class ScoreTimeAttackPenaltyAuthorPlus15Test(unittest.TestCase):
    def test_combined_scores(self):
        results = create_results_ta1()
        results_copy = deepcopy(results)
        sorting = ScoreTimeAttackPenaltyAuthorPlus15()
        results = sorting.combine_scores(
            [results, create_results_ta2()],
            [MatchInfo(medal_author=10000), MatchInfo(medal_author=32000)],
        )
        self.assertNotEqual(results, results_copy)
        self.assertEqual(6, len(results))

    def test_sort_scores(self):
        results = create_results_ta1()
        sorting = ScoreTimeAttackPenaltyAuthorPlus15()
        results = sorting.combine_scores(
            [results, create_results_ta2()],
            [MatchInfo(medal_author=10000), MatchInfo(medal_author=32000)],
        )
        results_copy = deepcopy(results)
        results = sorting.sort_scores(results)
        self.assertNotEqual(results, results_copy)
        self.assertEqual(6, len(results))
        self.assertEqual("p02", results[0].login)
        self.assertEqual("p06", results[1].login)
        self.assertEqual("p01", results[2].login)
        self.assertEqual("p03", results[3].login)
        self.assertEqual("p05", results[4].login)
        self.assertEqual("p04", results[5].login)
        self.assertEqual(47215 + 24926, results[0].player_score)
        self.assertEqual(10000 + 15000 + 47641, results[1].player_score)
        self.assertEqual(49502 + 25103, results[2].player_score)
        self.assertEqual(49897 + 26379, results[3].player_score)
        self.assertEqual(47641 + 32000 + 15000, results[4].player_score)
        self.assertEqual(48163 + 32000 + 15000, results[5].player_score)

    def test_update_placement(self):
        results = create_results_ta1()
        sorting = ScoreTimeAttackPenaltyAuthorPlus15()
        results = sorting.combine_scores(
            [results, create_results_ta2()],
            [MatchInfo(medal_author=10000), MatchInfo(medal_author=32000)],
        )
        results = sorting.sort_scores(results)
        results_copy = deepcopy(results)
        results = sorting.update_placements(results)
        self.assertNotEqual(results, results_copy)
        self.assertEqual(6, len(results))
        self.assertEqual(1, results[0].placement)
        self.assertEqual(2, results[1].placement)
        self.assertEqual(3, results[2].placement)
        self.assertEqual(4, results[3].placement)
        self.assertEqual(5, results[4].placement)
        self.assertEqual(6, results[5].placement)


if __name__ == "__main__":
    unittest.main()
