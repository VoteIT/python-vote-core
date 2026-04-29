from __future__ import annotations

from typing import Any

from pygraph.classes.digraph import digraph  # type: ignore[import-untyped]

from .abstract_classes import Ballot
from .abstract_classes import OrderingVotingSystem
from .schulze_helper import SchulzeHelper
from .tie_breaker import TieBreaker


class SchulzePR(OrderingVotingSystem, SchulzeHelper):
    def __init__(
        self,
        ballots: list[Ballot],
        tie_breaker: TieBreaker | list[Any] | None = None,
        winner_threshold: int | None = None,
        ballot_notation: int | None = None,
    ) -> None:
        self.standardize_ballots(ballots, ballot_notation)
        super().__init__(self.ballots, tie_breaker=tie_breaker, winner_threshold=winner_threshold)

    def calculate_results(self) -> None:
        remaining_candidates = self.candidates.copy()
        self.order: list[Any] = []
        self.rounds: list[dict[str, Any]] = []

        if self.winner_threshold is None:
            winner_threshold = len(self.candidates)
        else:
            winner_threshold = min(len(self.candidates), self.winner_threshold + 1)

        for self.required_winners in range(1, winner_threshold):  # type: ignore[attr-defined]
            self.generate_completed_patterns()
            self.generate_vote_management_graph()

            self.graph = digraph()
            self.graph.add_nodes(remaining_candidates)
            self.winners: set[Any] = set()
            self.tied_winners: set[Any] = set()

            for candidate_from in remaining_candidates:
                other_candidates = sorted(list(remaining_candidates - {candidate_from}))
                for candidate_to in other_candidates:
                    completed = self.proportional_completion(
                        candidate_from, {candidate_to} | set(self.order)
                    )
                    weight = self.strength_of_vote_management(completed)
                    if weight > 0:
                        self.graph.add_edge((candidate_to, candidate_from), weight)

            self.schwartz_set_heuristic()

            self.order.append(self.winner)  # type: ignore[attr-defined]
            round: dict[str, Any] = {"winner": self.winner}  # type: ignore[attr-defined]
            if len(self.tied_winners) > 0:
                round["tied_winners"] = self.tied_winners
            self.rounds.append(round)
            remaining_candidates -= {self.winner}  # type: ignore[attr-defined]
            del self.winner  # type: ignore[attr-defined]
            del self.actions  # type: ignore[attr-defined]
            if hasattr(self, "tied_winners"):
                del self.tied_winners

        if self.winner_threshold is None or self.winner_threshold == len(self.candidates):
            self.rounds.append({"winner": list(remaining_candidates)[0]})
            self.order.append(list(remaining_candidates)[0])

        del self.winner_threshold

    def as_dict(self) -> dict[str, Any]:
        data = super().as_dict()
        data["rounds"] = self.rounds
        return data
