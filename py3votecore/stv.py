from __future__ import annotations

import copy
import math
from typing import Any

from .abstract_classes import Ballot
from .abstract_classes import MultipleWinnerVotingSystem
from .common_functions import matching_keys
from .tie_breaker import TieBreaker


class STV(MultipleWinnerVotingSystem):
    def __init__(
        self,
        ballots: list[Ballot],
        tie_breaker: TieBreaker | list[Any] | None = None,
        required_winners: int = 1,
    ) -> None:
        super().__init__(ballots, tie_breaker=tie_breaker, required_winners=required_winners)

    def calculate_results(self) -> None:
        self.candidates: set[Any] = set()
        for ballot in self.ballots:
            ballot["count"] = float(ballot["count"])
            self.candidates.update(ballot["ballot"])
        if len(self.candidates) < self.required_winners:
            raise Exception("Not enough candidates provided")

        self.quota = STV.droop_quota(self.ballots, self.required_winners)
        self.rounds: list[dict[str, Any]] = []
        self.winners: set[Any] = set()
        quota = self.quota
        ballots = copy.deepcopy(self.ballots)
        remaining_candidates = self.candidates - self.winners

        while (
            len(self.winners) < self.required_winners
            and len(remaining_candidates) + len(self.winners) != self.required_winners
        ):
            if not remaining_candidates:
                remaining_candidates = self.candidates - self.winners

            round: dict[str, Any] = {}
            if len([ballot for ballot in ballots if ballot["count"] > 0 and ballot["ballot"]]) == 0:
                remaining_candidates = self.candidates - self.winners
                round["note"] = "reset"
                ballots = copy.deepcopy(self.ballots)
                for ballot in ballots:
                    ballot["ballot"] = [x for x in ballot["ballot"] if x in remaining_candidates]
                quota = STV.droop_quota(ballots, self.required_winners - len(self.winners))

            round["tallies"] = self.tallies(ballots)
            if round["tallies"]:
                if max(round["tallies"].values()) >= quota:
                    round["winners"] = {
                        candidate
                        for candidate, tally in round["tallies"].items()
                        if tally >= self.quota
                    }
                    self.winners |= round["winners"]
                    remaining_candidates -= round["winners"]

                    for ballot in ballots:
                        if ballot["ballot"] and ballot["ballot"][0] in round["winners"]:
                            ballot["count"] *= (
                                round["tallies"][ballot["ballot"][0]] - self.quota
                            ) / round["tallies"][ballot["ballot"][0]]

                    ballots = self.remove_candidates_from_ballots(round["winners"], ballots)

                else:
                    round.update(self.loser(round["tallies"]))
                    remaining_candidates.remove(round["loser"])
                    ballots = self.remove_candidates_from_ballots([round["loser"]], ballots)

            self.rounds.append(round)

        if len(self.winners) < self.required_winners:
            self.remaining_candidates = remaining_candidates
            self.winners |= self.remaining_candidates

    def as_dict(self) -> dict[str, Any]:
        data = super().as_dict()
        data["quota"] = self.quota
        data["rounds"] = self.rounds
        if hasattr(self, "remaining_candidates"):
            data["remaining_candidates"] = self.remaining_candidates
        return data

    def loser(self, tallies: dict[Any, float]) -> dict[str, Any]:
        losers = matching_keys(tallies, min(tallies.values()))
        if len(losers) == 1:
            return {"loser": list(losers)[0]}
        else:
            return {
                "tied_losers": losers,
                "loser": self.break_ties(losers, True),
            }

    @staticmethod
    def remove_candidates_from_ballots(
        candidates: set[Any] | list[Any], ballots: list[Ballot]
    ) -> list[Ballot]:
        for ballot in ballots:
            for candidate in candidates:
                if candidate in ballot["ballot"]:
                    ballot["ballot"].remove(candidate)
        return ballots

    def tallies(self, ballots: list[Ballot]) -> dict[Any, float]:
        tallies: dict[Any, float] = {
            candidate: 0.0 for ballot in ballots for candidate in ballot["ballot"]
        }
        for ballot in ballots:
            if ballot["ballot"]:
                tallies[ballot["ballot"][0]] += ballot["count"]
        return tallies

    @staticmethod
    def droop_quota(ballots: list[Ballot], seats: int = 1) -> int:
        voters = sum(ballot["count"] for ballot in ballots if ballot["ballot"])
        return int(math.floor(voters / (seats + 1)) + 1)
