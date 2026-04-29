from __future__ import annotations

from copy import deepcopy
from typing import Any

from pygraph.algorithms.cycles import find_cycle  # type: ignore[import-untyped]
from pygraph.classes.digraph import digraph  # type: ignore[import-untyped]

from .abstract_classes import Ballot
from .common_functions import matching_keys
from .condorcet import CondorcetHelper
from .condorcet import CondorcetSystem
from .tie_breaker import TieBreaker


class RankedPairs(CondorcetSystem, CondorcetHelper):
    def __init__(
        self,
        ballots: list[Ballot],
        tie_breaker: TieBreaker | list[Any] | None = None,
        ballot_notation: int | None = None,
    ) -> None:
        super().__init__(ballots, tie_breaker=tie_breaker, ballot_notation=ballot_notation)

    def condorcet_completion_method(self) -> None:
        self.rounds: list[dict[str, Any]] = []
        graph = digraph()
        graph.add_nodes(self.candidates)

        remaining_strong_pairs = deepcopy(self.strong_pairs)
        while len(remaining_strong_pairs) > 0:
            r: dict[str, Any] = {}

            largest_strength = max(remaining_strong_pairs.values())
            strongest_pairs = matching_keys(remaining_strong_pairs, largest_strength)
            if len(strongest_pairs) > 1:
                r["tied_pairs"] = strongest_pairs
                strongest_pair = self.break_ties(strongest_pairs)
            else:
                strongest_pair = list(strongest_pairs)[0]
            r["pair"] = strongest_pair

            graph.add_edge(strongest_pair)
            if len(find_cycle(graph)) > 0:
                r["action"] = "skipped"
                graph.del_edge(strongest_pair)
            else:
                r["action"] = "added"
            del remaining_strong_pairs[strongest_pair]
            self.rounds.append(r)

        self.old_graph = self.graph
        self.graph = graph
        self.graph_winner()

    def as_dict(self) -> dict[str, Any]:
        data = super().as_dict()
        if hasattr(self, "rounds"):
            data["rounds"] = self.rounds
        return data
