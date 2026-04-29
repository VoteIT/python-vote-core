from __future__ import annotations

from typing import Any

from .abstract_classes import AbstractSingleWinnerVotingSystem
from .abstract_classes import Ballot
from .plurality_at_large import PluralityAtLarge
from .tie_breaker import TieBreaker


class Plurality(AbstractSingleWinnerVotingSystem):
    def __init__(
        self, ballots: list[Ballot], tie_breaker: TieBreaker | list[Any] | None = None
    ) -> None:
        super().__init__(ballots, PluralityAtLarge, tie_breaker=tie_breaker)
