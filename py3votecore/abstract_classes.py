from __future__ import annotations

from abc import ABC
from abc import abstractmethod
from collections.abc import Iterable
from copy import copy
from copy import deepcopy
from typing import Any
from typing import TypeAlias

from .tie_breaker import TieBreaker

Ballot: TypeAlias = dict[str, Any]


class VotingSystem(ABC):
    candidates: set[Any]
    tie_breaker: TieBreaker | None
    ballots: list[Ballot]

    @abstractmethod
    def __init__(
        self, ballots: list[Ballot], tie_breaker: TieBreaker | list[Any] | None = None
    ) -> None:
        self.ballots = ballots
        for ballot in self.ballots:
            if "count" not in ballot:
                ballot["count"] = 1
        if isinstance(tie_breaker, list):
            self.tie_breaker = TieBreaker(tie_breaker)
        else:
            self.tie_breaker = tie_breaker
        self.calculate_results()

    @abstractmethod
    def calculate_results(self) -> None: ...

    @abstractmethod
    def as_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        data["candidates"] = self.candidates
        if self.tie_breaker and self.tie_breaker.ties_broken:
            data["tie_breaker"] = self.tie_breaker.as_list()
        return data

    def break_ties(self, tied_objects: Iterable[Any], reverse_order: bool = False) -> Any:
        if self.tie_breaker is None:
            self.tie_breaker = TieBreaker(self.candidates)
        return self.tie_breaker.break_ties(tied_objects, reverse_order)


class FixedWinnerVotingSystem(VotingSystem, ABC):
    @abstractmethod
    def __init__(
        self, ballots: list[Ballot], tie_breaker: TieBreaker | list[Any] | None = None
    ) -> None:
        super().__init__(ballots, tie_breaker)

    def as_dict(self) -> dict[str, Any]:
        data = super().as_dict()
        if hasattr(self, "tied_winners"):
            data["tied_winners"] = self.tied_winners  # type: ignore[attr-defined]
        return data


class MultipleWinnerVotingSystem(FixedWinnerVotingSystem, ABC):
    winners: set[Any]

    @abstractmethod
    def __init__(
        self,
        ballots: list[Ballot],
        tie_breaker: TieBreaker | list[Any] | None = None,
        required_winners: int = 1,
    ) -> None:
        self.required_winners = required_winners
        super().__init__(ballots, tie_breaker)

    def calculate_results(self) -> None:
        if self.required_winners == len(self.candidates):
            self.winners = self.candidates

    def as_dict(self) -> dict[str, Any]:
        data = super().as_dict()
        data["winners"] = self.winners
        return data


class SingleWinnerVotingSystem(FixedWinnerVotingSystem, ABC):
    winner: Any

    @abstractmethod
    def __init__(
        self, ballots: list[Ballot], tie_breaker: TieBreaker | list[Any] | None = None
    ) -> None:
        super().__init__(ballots, tie_breaker)

    def as_dict(self) -> dict[str, Any]:
        data = super().as_dict()
        data["winner"] = self.winner
        return data


class AbstractSingleWinnerVotingSystem(SingleWinnerVotingSystem, ABC):
    rounds: list[dict[str, Any]]

    @abstractmethod
    def __init__(
        self,
        ballots: list[Ballot],
        multiple_winner_class: type[MultipleWinnerVotingSystem],
        tie_breaker: TieBreaker | list[Any] | None = None,
    ) -> None:
        self.multiple_winner_class = multiple_winner_class
        super().__init__(ballots, tie_breaker=tie_breaker)

    def calculate_results(self) -> None:
        self.multiple_winner_instance = self.multiple_winner_class(
            self.ballots, tie_breaker=self.tie_breaker, required_winners=1
        )
        self.__dict__.update(self.multiple_winner_instance.__dict__)
        self.winner = list(self.winners)[0]  # type: ignore[attr-defined]
        del self.winners  # type: ignore[attr-defined]

    def as_dict(self) -> dict[str, Any]:
        data = super().as_dict()
        data.update(self.multiple_winner_instance.as_dict())
        del data["winners"]
        return data


class OrderingVotingSystem(VotingSystem, ABC):
    order: list[Any]

    @abstractmethod
    def __init__(
        self,
        ballots: list[Ballot],
        tie_breaker: TieBreaker | list[Any] | None = None,
        winner_threshold: int | None = None,
    ) -> None:
        self.winner_threshold = winner_threshold
        super().__init__(ballots, tie_breaker=tie_breaker)

    def as_dict(self) -> dict[str, Any]:
        data = super().as_dict()
        data["order"] = self.order
        return data


class AbstractOrderingVotingSystem(OrderingVotingSystem, ABC):
    @abstractmethod
    def __init__(
        self,
        ballots: list[Ballot],
        single_winner_class: type[SingleWinnerVotingSystem],
        winner_threshold: int | None = None,
        tie_breaker: TieBreaker | list[Any] | None = None,
    ) -> None:
        self.single_winner_class = single_winner_class
        super().__init__(ballots, winner_threshold=winner_threshold, tie_breaker=tie_breaker)

    @abstractmethod
    def ballots_without_candidate(self, ballots: list[Ballot], candidate: Any) -> list[Ballot]: ...

    def calculate_results(self) -> None:
        self.order = []
        self.rounds: list[dict[str, Any]] = []
        remaining_ballots = deepcopy(self.ballots)
        remaining_candidates: set[Any] | None = None
        while (remaining_candidates is None or len(remaining_candidates) > 1) and (
            self.winner_threshold is None or len(self.order) < self.winner_threshold
        ):
            result = self.single_winner_class(
                deepcopy(remaining_ballots), tie_breaker=self.tie_breaker
            )
            r: dict[str, Any] = {"winner": result.winner}
            self.order.append(r["winner"])

            if hasattr(result, "tie_breaker"):
                self.tie_breaker = result.tie_breaker
                if hasattr(result, "tied_winners"):
                    r["tied_winners"] = result.tied_winners
            self.rounds.append(r)

            if remaining_candidates is None:
                self.candidates = result.candidates
                remaining_candidates = copy(self.candidates)
            remaining_candidates.remove(result.winner)
            remaining_ballots = self.ballots_without_candidate(result.ballots, result.winner)

        if self.winner_threshold is None or len(self.order) < self.winner_threshold:
            assert remaining_candidates is not None
            r = {"winner": list(remaining_candidates)[0]}
            self.order.append(r["winner"])
            self.rounds.append(r)

    def as_dict(self) -> dict[str, Any]:
        data = super().as_dict()
        data["rounds"] = self.rounds
        return data
