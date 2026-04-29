from __future__ import annotations

import itertools
from typing import Any

from pygraph.classes.digraph import digraph  # type: ignore[import-untyped]

from .abstract_classes import Ballot
from .abstract_classes import MultipleWinnerVotingSystem
from .schulze_helper import SchulzeHelper
from .tie_breaker import TieBreaker


class SchulzeSTV(MultipleWinnerVotingSystem, SchulzeHelper):
    def __init__(
        self,
        ballots: list[Ballot],
        tie_breaker: TieBreaker | list[Any] | None = None,
        required_winners: int = 1,
        ballot_notation: int | None = None,
    ) -> None:
        self.standardize_ballots(ballots, ballot_notation)
        super().__init__(self.ballots, tie_breaker=tie_breaker, required_winners=required_winners)

    def calculate_results(self) -> None:
        super().calculate_results()
        if hasattr(self, "winners"):
            return

        self.generate_completed_patterns()
        self.generate_vote_management_graph()

        self.graph = digraph()
        for candidate_set in itertools.combinations(self.candidates, self.required_winners):
            self.graph.add_nodes([tuple(sorted(list(candidate_set)))])

        for candidate_set in itertools.combinations(self.candidates, self.required_winners + 1):
            for candidate in candidate_set:
                other_candidates = sorted(set(candidate_set) - {candidate})
                completed = self.proportional_completion(candidate, other_candidates)
                weight = self.strength_of_vote_management(completed)
                if weight > 0:
                    for subset in itertools.combinations(
                        other_candidates, len(other_candidates) - 1
                    ):
                        self.graph.add_edge(
                            (
                                tuple(other_candidates),
                                tuple(sorted(list(subset) + [candidate])),
                            ),
                            weight,
                        )

        self.graph_winner()

        self.winners = set(self.winner)  # type: ignore[attr-defined]
        del self.winner  # type: ignore[attr-defined]

    def as_dict(self) -> dict[str, Any]:
        data = super().as_dict()
        if hasattr(self, "actions"):
            data["actions"] = self.actions
        return data
