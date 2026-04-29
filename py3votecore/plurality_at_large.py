from __future__ import annotations

import copy
from typing import Any

from .abstract_classes import Ballot
from .abstract_classes import MultipleWinnerVotingSystem
from .common_functions import matching_keys
from .tie_breaker import TieBreaker


class PluralityAtLarge(MultipleWinnerVotingSystem):
    def __init__(
        self,
        ballots: list[Ballot],
        tie_breaker: TieBreaker | list[Any] | None = None,
        required_winners: int = 1,
    ) -> None:
        super().__init__(ballots, tie_breaker=tie_breaker, required_winners=required_winners)

    def calculate_results(self) -> None:
        self.candidates = set()
        for ballot in self.ballots:
            if not isinstance(ballot["ballot"], list):
                ballot["ballot"] = [ballot["ballot"]]

            if len(ballot["ballot"]) > self.required_winners:
                raise Exception("A ballot contained too many candidates")

            self.candidates.update(set(ballot["ballot"]))

        self.tallies: dict[Any, int | float] = dict.fromkeys(self.candidates, 0)
        for ballot in self.ballots:
            for candidate in ballot["ballot"]:
                self.tallies[candidate] += ballot["count"]
        tallies = copy.deepcopy(self.tallies)

        winning_candidates: set[Any] = set()
        while len(winning_candidates) < self.required_winners:
            largest_tally = max(tallies.values())
            top_candidates = matching_keys(tallies, largest_tally)

            if len(top_candidates | winning_candidates) > self.required_winners:
                self.tied_winners = top_candidates.copy()
                while len(top_candidates | winning_candidates) > self.required_winners:
                    top_candidates.remove(self.break_ties(top_candidates, True))

            winning_candidates |= top_candidates
            for candidate in top_candidates:
                del tallies[candidate]

        self.winners = winning_candidates

    def as_dict(self) -> dict[str, Any]:
        data = super().as_dict()
        data["tallies"] = self.tallies
        return data
