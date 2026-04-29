from __future__ import annotations

from typing import Any

from .abstract_classes import Ballot
from .condorcet import CondorcetSystem
from .schulze_helper import SchulzeHelper
from .tie_breaker import TieBreaker


class SchulzeMethod(CondorcetSystem, SchulzeHelper):
    def __init__(
        self,
        ballots: list[Ballot],
        tie_breaker: TieBreaker | list[Any] | None = None,
        ballot_notation: int | None = None,
    ) -> None:
        super().__init__(ballots, tie_breaker=tie_breaker, ballot_notation=ballot_notation)

    def as_dict(self) -> dict[str, Any]:
        data = super().as_dict()
        if hasattr(self, "actions"):
            data["actions"] = self.actions
        return data
