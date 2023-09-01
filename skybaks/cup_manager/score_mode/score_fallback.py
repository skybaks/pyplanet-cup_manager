import logging

from ..app_types import TeamPlayerScore
from ..models import MatchInfo
from .score_base import ScoreModeBase


class ScoreModeFallback(ScoreModeBase):
    """
    Score sorting mode for general use. This mode is used when no other default
    mode determination can be made.

    Both team score and player score are used in sorting and determining
    rankings. However, if team score is found to be zero for all players then it
    will be hidden from display to reduce clutter.


    Recommended Modes: Any player or team-based mode which uses points
    Sorting: Team score descending, Score descending
    """

    def __init__(self) -> None:
        super().__init__()
        self.name = "score_mode_fallback"
        self.display_name = "Default Fallback Mode"
        self.brief = "Fallback when no other default mode has been determined"
        self.score1_is_time = False
        self.score2_is_time = False
        self.scoreteam_is_time = False
        self.use_score1 = True
        self.use_score2 = False
        self.use_scoreteam = True
        self.score_names.score1_name = "Point(s)"
        self.score_names.scoreteam_name = "Point(s)"

    def combine_scores(
        self,
        scores: "list[list[TeamPlayerScore]]",
        maps: "list[MatchInfo]" = [],
        **kwargs
    ) -> "list[TeamPlayerScore]":
        combined_scores = []  # type: list[TeamPlayerScore]
        for map_scores in scores:
            for map_score in map_scores:
                existing_score = next(
                    (x for x in combined_scores if x.login == map_score.login), None
                )
                if existing_score:
                    existing_score.team_score += map_score.team_score
                    existing_score.player_score += map_score.player_score
                else:
                    combined_scores.append(map_score)

        # Hide team scores if there are no team points
        self.use_scoreteam = any(s.team_score > 0 for s in combined_scores)
        return combined_scores

    def sort_scores(self, scores: "list[TeamPlayerScore]") -> "list[TeamPlayerScore]":
        return sorted(scores, key=lambda x: (-x.team_score, -x.player_score))

    def update_placements(
        self, scores: "list[TeamPlayerScore]"
    ) -> "list[TeamPlayerScore]":
        for i in range(0, len(scores)):
            if i > 0:
                if (
                    scores[i - 1].team_score == scores[i].team_score
                    and scores[i - 1].player_score == scores[i].player_score
                ):
                    scores[i].placement = scores[i - 1].placement
                else:
                    scores[i].placement = i + 1
            else:
                scores[i].placement = i + 1
        return scores
