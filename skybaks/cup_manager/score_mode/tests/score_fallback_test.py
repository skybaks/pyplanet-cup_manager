import unittest
from copy import deepcopy

from ...app_types import TeamPlayerScore
from ...models import MatchInfo
from ..score_fallback import ScoreModeFallback


def create_results() -> "list[TeamPlayerScore]":
    results = [
        TeamPlayerScore("p01", "player 01", "France", -1, "", 0, 121, 0),
        TeamPlayerScore("p02", "player 02", "France", -1, "", 0, 150, 0),  # tie
        TeamPlayerScore("p03", "player 03", "France", -1, "", 0, 149, 0),
        TeamPlayerScore("p04", "player 04", "France", -1, "", 0, 134, 0),
        TeamPlayerScore("p05", "player 05", "France", -1, "", 0, 267, 0),
        TeamPlayerScore("p06", "player 06", "France", -1, "", 0, 201, 0),
        TeamPlayerScore("p07", "player 07", "France", -1, "", 0, 150, 0),  # tie
    ]
    return results


def create_results2() -> "list[TeamPlayerScore]":
    results = [
        TeamPlayerScore("p01", "player 01", "France", -1, "", 0, 130, 0),
        TeamPlayerScore("p02", "player 02", "France", -1, "", 0, 140, 0),
        TeamPlayerScore("p03", "player 03", "France", -1, "", 0, 170, 0),
        TeamPlayerScore("p04", "player 04", "France", -1, "", 0, 160, 0),
        TeamPlayerScore("p05", "player 05", "France", -1, "", 0, 123, 0),
        TeamPlayerScore("p06", "player 06", "France", -1, "", 0, 104, 0),
        TeamPlayerScore("p07", "player 07", "France", -1, "", 0, 129, 0),
    ]
    return results


def create_results3() -> "list[TeamPlayerScore]":
    return [
        TeamPlayerScore("p01", "player 01", "France", 1, "Red", 3, 26, 0),
        TeamPlayerScore("p02", "player 02", "France", 1, "Red", 3, 19, 0),
        TeamPlayerScore("p03", "player 03", "France", 2, "Blu", 4, 19, 0),
        TeamPlayerScore("p04", "player 04", "France", 2, "Blu", 4, 21, 0),
        TeamPlayerScore("p05", "player 05", "France", 1, "Red", 3, 19, 0),
    ]


class ScoreModeFallbackTest(unittest.TestCase):
    def test_combine_scores(self):
        results = create_results2()
        results_copy = deepcopy(results)
        sorting = ScoreModeFallback()
        results = sorting.combine_scores([results, create_results3()])
        self.assertNotEqual(results, results_copy)
        self.assertEqual(7, len(results))
        self.assertEqual("p01", results[0].login)
        self.assertEqual("p02", results[1].login)
        self.assertEqual("p03", results[2].login)
        self.assertEqual("p04", results[3].login)
        self.assertEqual("p05", results[4].login)
        self.assertEqual("p06", results[5].login)
        self.assertEqual("p07", results[6].login)
        self.assertEqual(0 + 3, results[0].team_score)
        self.assertEqual(0 + 3, results[1].team_score)
        self.assertEqual(0 + 4, results[2].team_score)
        self.assertEqual(0 + 4, results[3].team_score)
        self.assertEqual(0 + 3, results[4].team_score)
        self.assertEqual(0 + 0, results[5].team_score)
        self.assertEqual(0 + 0, results[6].team_score)
        self.assertEqual(130 + 26, results[0].player_score)
        self.assertEqual(140 + 19, results[1].player_score)
        self.assertEqual(170 + 19, results[2].player_score)
        self.assertEqual(160 + 21, results[3].player_score)
        self.assertEqual(123 + 19, results[4].player_score)
        self.assertEqual(104 + 0, results[5].player_score)
        self.assertEqual(129 + 0, results[6].player_score)

    def test_sort_scores(self):
        results = create_results3()
        results_copy = deepcopy(results)
        sorting = ScoreModeFallback()
        results = sorting.sort_scores(results)
        self.assertNotEqual(results, results_copy)
        self.assertEqual("p04", results[0].login)
        self.assertEqual("p03", results[1].login)
        self.assertEqual("p01", results[2].login)
        self.assertEqual("p02", results[3].login)
        self.assertEqual("p05", results[4].login)

    def test_update_placement(self):
        sorting = ScoreModeFallback()
        results = sorting.sort_scores(create_results3())
        results_copy = deepcopy(results)
        results = sorting.update_placements(results)
        self.assertNotEqual(results, results_copy)
        self.assertEqual(1, results[0].placement)
        self.assertEqual(2, results[1].placement)
        self.assertEqual(3, results[2].placement)
        self.assertEqual(4, results[3].placement)
        self.assertEqual(4, results[4].placement)

    def test_get_ties(self):
        sorting = ScoreModeFallback()
        results = sorting.sort_scores(create_results3())
        results = sorting.update_placements(results)
        ties = sorting.get_ties(results)
        self.assertEqual(2, len(ties))
        self.assertTrue("p02" in ties)
        self.assertEqual(1, len(ties["p02"]))
        self.assertEqual("p05", ties["p02"][0].login)
        self.assertTrue("p05" in ties)
        self.assertEqual(1, len(ties["p05"]))
        self.assertEqual("p02", ties["p05"][0].login)

    def test_update_score_is_time(self):
        sorting = ScoreModeFallback()
        results = sorting.update_score_is_time(create_results3())
        for result in results:
            self.assertFalse(result.player_score_is_time)
            self.assertFalse(result.player_score2_is_time)
            self.assertFalse(result.team_score_is_time)

    def test_score1_relevant(self):
        sorting = ScoreModeFallback()
        self.assertTrue(sorting.score1_relevant())

    def test_score2_relevant(self):
        sorting = ScoreModeFallback()
        self.assertFalse(sorting.score2_relevant())

    def test_scoreteam_relevant(self):
        sorting = ScoreModeFallback()
        self.assertTrue(sorting.scoreteam_relevant())

    def test_scoreteam_relevant_disabled(self):
        sorting = ScoreModeFallback()
        self.assertTrue(sorting.scoreteam_relevant())
        results = sorting.combine_scores([create_results(), create_results2()])
        self.assertFalse(sorting.scoreteam_relevant())
        results = sorting.combine_scores(
            [create_results(), create_results2(), create_results3()]
        )
        self.assertTrue(sorting.scoreteam_relevant())

    def test_relevant_score_str(self):
        sorting = ScoreModeFallback()
        score = TeamPlayerScore("p01", "name01", "Any", 1, "Red", 6, 63, 0)
        results = sorting.update_score_is_time([score])
        results_str = sorting.relevant_score_str(results[0])
        self.assertEqual("6,63", results_str)
        results_str = sorting.relevant_score_str(results[0], "$fff")
        self.assertEqual("$<$fff6$>,$<$fff63$>", results_str)

    def test_diff_scores_str(self):
        sorting = ScoreModeFallback()
        results = sorting.update_score_is_time(create_results3())
        results_str = sorting.diff_scores_str(results[0], results[1])
        self.assertEqual("0, 7", results_str)


if __name__ == "__main__":
    unittest.main()
