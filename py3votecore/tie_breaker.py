import random
from collections.abc import Iterable
from copy import copy
from typing import Any


class TieBreaker:
    def __init__(self, candidate_range: Iterable[Any]) -> None:
        self.ties_broken = False
        self.random_ordering: list[Any] = list(candidate_range)
        if not isinstance(candidate_range, list):
            random.shuffle(self.random_ordering)

    def break_ties(self, tied_candidates: Iterable[Any], reverse: bool = False) -> Any:
        self.ties_broken = True
        random_ordering = copy(self.random_ordering)
        if reverse:
            random_ordering.reverse()
        # The following line is from @gleb-chipiga
        if isinstance(list(tied_candidates)[0], tuple):
            result = self.break_complex_ties(tied_candidates, random_ordering)
        else:
            result = self.break_simple_ties(tied_candidates, random_ordering)
        return result

    @staticmethod
    def break_simple_ties(tied_candidates: Iterable[Any], random_ordering: list[Any]) -> Any:
        for candidate in random_ordering:
            if candidate in tied_candidates:
                return candidate

    @staticmethod
    def break_complex_ties(tied_candidates: Iterable[Any], random_ordering: list[Any]) -> Any:
        remaining = set(tied_candidates)
        max_columns = len(list(remaining)[0])
        column = 0
        while len(remaining) > 1 and column < max_columns:
            min_index = min(
                random_ordering.index(list(candidate)[column]) for candidate in remaining
            )
            remaining = {
                candidate
                for candidate in remaining
                if candidate[column] == random_ordering[min_index]
            }
            column += 1
        return list(remaining)[0]

    def as_list(self) -> list[Any]:
        return self.random_ordering

    def __str__(self) -> str:
        return f"[{'>'.join(self.random_ordering)}]"
