from __future__ import annotations

from typing import Any

from pygraph.classes.digraph import digraph  # type: ignore[import-untyped]

from .abstract_classes import AbstractOrderingVotingSystem
from .abstract_classes import Ballot
from .schulze_helper import SchulzeHelper
from .schulze_method import SchulzeMethod
from .tie_breaker import TieBreaker


class SchulzeMethodByGraph(SchulzeMethod):
    def __init__(
        self,
        edges: dict[tuple[Any, Any], float],
        tie_breaker: TieBreaker | list[Any] | None = None,
        ballot_notation: int | None = None,
    ) -> None:
        self.edges = edges
        super().__init__([], tie_breaker=tie_breaker, ballot_notation=ballot_notation)

    def standardize_ballots(self, ballots: list[Ballot], ballot_notation: int | None) -> None:
        self.ballots = []
        self.candidates = {edge[0] for edge in self.edges} | {edge[1] for edge in self.edges}

    def ballots_into_graph(self, candidates: set[Any], ballots: list[Ballot]) -> digraph:  # type: ignore[override]
        graph = digraph()
        graph.add_nodes(candidates)
        for edge in self.edges.items():
            graph.add_edge(edge[0], edge[1])
        return graph


class SchulzeNPRByGraph(AbstractOrderingVotingSystem, SchulzeHelper):
    def __init__(
        self,
        edges: dict[tuple[Any, Any], float],
        winner_threshold: int | None = None,
        tie_breaker: TieBreaker | list[Any] | None = None,
        ballot_notation: int | None = None,
    ) -> None:
        self.edges = edges
        self.candidates = {edge[0] for edge in edges} | {edge[1] for edge in edges}
        super().__init__(
            [],
            single_winner_class=SchulzeMethodByGraph,  # type: ignore[arg-type]
            winner_threshold=winner_threshold,
            tie_breaker=tie_breaker,
        )

    def ballots_without_candidate(self, ballots: list[Ballot], candidate: Any) -> list[Ballot]:  # type: ignore[override]
        self.edges = {
            edge: weight
            for edge, weight in self.edges.items()
            if edge[0] != candidate and edge[1] != candidate
        }
        return self.edges  # type: ignore[return-value]

    def calculate_results(self) -> None:
        self.ballots = self.edges  # type: ignore[assignment]
        super().calculate_results()
