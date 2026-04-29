from collections.abc import Generator
from typing import Any


def matching_keys(d: dict[Any, Any], target_value: Any) -> set[Any]:
    return {key for key, value in d.items() if value == target_value}


def unique_permutations(xs: list[Any]) -> Generator[list[Any], None, None]:
    if len(xs) < 2:
        yield xs
    else:
        h: list[Any] = []
        for x in xs:
            h.append(x)
            if x in h[:-1]:
                continue
            ts = xs[:]
            ts.remove(x)
            for ps in unique_permutations(ts):
                yield [x] + ps
