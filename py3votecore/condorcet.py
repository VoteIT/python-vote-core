from __future__ import annotations

import copy
import itertools
from abc import ABC
from abc import abstractmethod
from typing import Any

from pygraph.classes.digraph import digraph  # type: ignore[import-untyped]

from .abstract_classes import Ballot
from .abstract_classes import SingleWinnerVotingSystem
from .tie_breaker import TieBreaker


class CondorcetHelper:
    BALLOT_NOTATION_GROUPING = 0
    BALLOT_NOTATION_RANKING = 1
    BALLOT_NOTATION_RATING = 2

    ballots: list[Ballot]
    candidates: set[Any]

    def standardize_ballots(self, ballots: list[Ballot], ballot_notation: int | None) -> None:
        self.ballots = copy.deepcopy(ballots)
        if ballot_notation == CondorcetHelper.BALLOT_NOTATION_GROUPING:
            for ballot in self.ballots:
                new_ballot: dict[Any, float] = {}
                r = len(ballot["ballot"])
                for rank in ballot["ballot"]:
                    for candidate in rank:
                        new_ballot[candidate] = r
                    r -= 1
                ballot["ballot"] = new_ballot
        elif ballot_notation == CondorcetHelper.BALLOT_NOTATION_RANKING:
            for ballot in self.ballots:
                for candidate, rating in ballot["ballot"].items():
                    ballot["ballot"][candidate] = -float(rating)
        elif ballot_notation == CondorcetHelper.BALLOT_NOTATION_RATING or ballot_notation is None:
            for ballot in self.ballots:
                for candidate, rating in ballot["ballot"].items():
                    ballot["ballot"][candidate] = float(rating)
        else:
            raise Exception("Unknown notation specified", ballot_notation)

        self.candidates = set()
        for ballot in self.ballots:
            self.candidates |= set(ballot["ballot"].keys())

        for ballot in self.ballots:
            lowest_preference = min(ballot["ballot"].values()) - 1
            for candidate in self.candidates - set(ballot["ballot"].keys()):
                ballot["ballot"][candidate] = lowest_preference

    def graph_winner(self) -> None:
        losing_candidates = {edge[1] for edge in self.graph.edges()}  # type: ignore[attr-defined]
        winning_candidates = set(self.graph.nodes()) - losing_candidates  # type: ignore[attr-defined]
        if len(winning_candidates) == 1:
            self.winner = list(winning_candidates)[0]  # type: ignore[attr-defined]
        elif len(winning_candidates) > 1:
            self.tied_winners = winning_candidates  # type: ignore[attr-defined]
            self.winner = self.break_ties(winning_candidates)  # type: ignore[attr-defined]
        else:
            self.condorcet_completion_method()  # type: ignore[attr-defined]

    @staticmethod
    def ballots_into_graph(candidates: set[Any], ballots: list[Ballot]) -> digraph:
        graph = digraph()
        graph.add_nodes(candidates)
        for pair in itertools.permutations(candidates, 2):
            graph.add_edge(
                pair,
                sum(
                    [
                        ballot["count"]
                        for ballot in ballots
                        if ballot["ballot"][pair[0]] > ballot["ballot"][pair[1]]
                    ]
                ),
            )
        return graph

    @staticmethod
    def edge_weights(graph: digraph) -> dict[tuple[Any, Any], float]:
        return {edge: graph.edge_weight(edge) for edge in graph.edges()}

    @staticmethod
    def remove_weak_edges(graph: digraph) -> None:
        for pair in itertools.combinations(graph.nodes(), 2):
            pairs = (pair, (pair[1], pair[0]))
            weights = (graph.edge_weight(pairs[0]), graph.edge_weight(pairs[1]))
            if weights[0] >= weights[1]:
                graph.del_edge(pairs[1])
            if weights[1] >= weights[0]:
                graph.del_edge(pairs[0])


class CondorcetSystem(SingleWinnerVotingSystem, CondorcetHelper, ABC):
    graph: digraph

    @abstractmethod
    def __init__(
        self,
        ballots: list[Ballot],
        tie_breaker: TieBreaker | list[Any] | None = None,
        ballot_notation: int | None = None,
    ) -> None:
        self.standardize_ballots(ballots, ballot_notation)
        super().__init__(self.ballots, tie_breaker=tie_breaker)

    def calculate_results(self) -> None:
        self.graph = self.ballots_into_graph(self.candidates, self.ballots)
        self.pairs = self.edge_weights(self.graph)
        self.remove_weak_edges(self.graph)
        self.strong_pairs = self.edge_weights(self.graph)
        self.graph_winner()

    def as_dict(self) -> dict[str, Any]:
        data = super().as_dict()
        if hasattr(self, "pairs"):
            data["pairs"] = self.pairs
        if hasattr(self, "strong_pairs"):
            data["strong_pairs"] = self.strong_pairs
        if hasattr(self, "tied_winners"):
            data["tied_winners"] = self.tied_winners
        return data
