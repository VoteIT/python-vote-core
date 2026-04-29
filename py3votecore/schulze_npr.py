from __future__ import annotations

from typing import Any

from .abstract_classes import AbstractOrderingVotingSystem
from .abstract_classes import Ballot
from .schulze_helper import SchulzeHelper
from .schulze_method import SchulzeMethod
from .tie_breaker import TieBreaker


class SchulzeNPR(AbstractOrderingVotingSystem, SchulzeHelper):
    def __init__(
        self,
        ballots: list[Ballot],
        winner_threshold: int | None = None,
        tie_breaker: TieBreaker | list[Any] | None = None,
        ballot_notation: int | None = None,
    ) -> None:
        self.standardize_ballots(ballots, ballot_notation)
        super().__init__(
            self.ballots,
            single_winner_class=SchulzeMethod,
            winner_threshold=winner_threshold,
            tie_breaker=tie_breaker,
        )

    @staticmethod
    def ballots_without_candidate(ballots: list[Ballot], candidate: Any) -> list[Ballot]:  # type: ignore[override]
        for ballot in ballots:
            if candidate in ballot["ballot"]:
                del ballot["ballot"][candidate]
        return ballots
