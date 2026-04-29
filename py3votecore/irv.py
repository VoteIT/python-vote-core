from __future__ import annotations

from typing import Any

from .abstract_classes import AbstractSingleWinnerVotingSystem
from .abstract_classes import Ballot
from .stv import STV
from .tie_breaker import TieBreaker


class IRV(AbstractSingleWinnerVotingSystem):
    def __init__(
        self, ballots: list[Ballot], tie_breaker: TieBreaker | list[Any] | None = None
    ) -> None:
        super().__init__(ballots, STV, tie_breaker=tie_breaker)

    def calculate_results(self) -> None:
        super().calculate_results()
        IRV.singularize(self.rounds)

    def as_dict(self) -> dict[str, Any]:
        data = super().as_dict()
        IRV.singularize(data["rounds"])
        return data

    @staticmethod
    def singularize(rounds: list[dict[str, Any]]) -> None:
        for r in rounds:
            if "winners" in r:
                r["winner"] = list(r["winners"])[0]
                del r["winners"]
