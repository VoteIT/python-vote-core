from __future__ import annotations

from typing import Any

from pygraph.algorithms.accessibility import accessibility  # type: ignore[import-untyped]
from pygraph.algorithms.accessibility import mutual_accessibility  # type: ignore[import-untyped]
from pygraph.algorithms.minmax import maximum_flow  # type: ignore[import-untyped]
from pygraph.classes.digraph import digraph  # type: ignore[import-untyped]

from .common_functions import matching_keys
from .common_functions import unique_permutations
from .condorcet import CondorcetHelper

PREFERRED_LESS = 1
PREFERRED_SAME = 2
PREFERRED_MORE = 3
STRENGTH_TOLERANCE = 0.0000000001
STRENGTH_THRESHOLD = 0.1
NODE_SINK = -1
NODE_SOURCE = -2


class SchulzeHelper(CondorcetHelper):
    required_winners: int

    def condorcet_completion_method(self) -> None:
        self.schwartz_set_heuristic()

    def schwartz_set_heuristic(self) -> None:
        self.actions: list[dict[str, Any]] = []
        while len(self.graph.edges()) > 0:  # type: ignore[attr-defined]
            access = accessibility(self.graph)  # type: ignore[attr-defined]
            mutual_access = mutual_accessibility(self.graph)  # type: ignore[attr-defined]
            candidates_to_remove: set[Any] = set()
            for candidate in self.graph.nodes():  # type: ignore[attr-defined]
                candidates_to_remove |= set(access[candidate]) - set(mutual_access[candidate])

            if len(candidates_to_remove) > 0:
                self.actions.append({"nodes": candidates_to_remove})
                for candidate in candidates_to_remove:
                    self.graph.del_node(candidate)  # type: ignore[attr-defined]
            else:
                edge_weights = self.edge_weights(self.graph)  # type: ignore[attr-defined]
                self.actions.append(
                    {"edges": matching_keys(edge_weights, min(edge_weights.values()))}
                )
                for edge in self.actions[-1]["edges"]:
                    self.graph.del_edge(edge)  # type: ignore[attr-defined]

        self.graph_winner()

    def generate_vote_management_graph(self) -> None:
        self.vote_management_graph = digraph()
        self.vote_management_graph.add_nodes(self.completed_patterns)
        self.vote_management_graph.del_node(tuple([PREFERRED_MORE] * self.required_winners))  # type: ignore[attr-defined]
        self.pattern_nodes = self.vote_management_graph.nodes()
        self.vote_management_graph.add_nodes([NODE_SOURCE, NODE_SINK])
        for pattern_node in self.pattern_nodes:
            self.vote_management_graph.add_edge((NODE_SOURCE, pattern_node))
        for i in range(self.required_winners):  # type: ignore[attr-defined]
            self.vote_management_graph.add_node(i)
        for pattern_node in self.pattern_nodes:
            for i in range(self.required_winners):  # type: ignore[attr-defined]
                if pattern_node[i] == 1:
                    self.vote_management_graph.add_edge((pattern_node, i))
        for i in range(self.required_winners):  # type: ignore[attr-defined]
            self.vote_management_graph.add_edge((i, NODE_SINK))

    def generate_completed_patterns(self) -> None:
        self.completed_patterns: list[tuple[int, ...]] = []
        for i in range(0, self.required_winners + 1):  # type: ignore[attr-defined]
            for pattern in unique_permutations(
                [PREFERRED_LESS] * (self.required_winners - i)  # type: ignore[attr-defined]
                + [PREFERRED_MORE] * i
            ):
                self.completed_patterns.append(tuple(pattern))

    def proportional_completion(
        self, candidate: Any, other_candidates: set[Any] | list[Any]
    ) -> dict[tuple[int, ...], float]:
        profile: dict[tuple[int, ...], float] = dict(
            zip(self.completed_patterns, [0.0] * len(self.completed_patterns), strict=True)
        )

        for ballot in self.ballots:  # type: ignore[attr-defined]
            pattern: list[int] = []
            for other_candidate in other_candidates:
                if ballot["ballot"][candidate] < ballot["ballot"][other_candidate]:
                    pattern.append(PREFERRED_LESS)
                elif ballot["ballot"][candidate] == ballot["ballot"][other_candidate]:
                    pattern.append(PREFERRED_SAME)
                else:
                    pattern.append(PREFERRED_MORE)
            key = tuple(pattern)
            if key not in profile:
                profile[key] = 0.0
            profile[key] += ballot["count"]
        weight_sum = sum(profile.values())

        while True:
            m = max(pat.count(PREFERRED_SAME) for pat in profile)
            if m == 0:
                break
            for pat in list(profile.keys()):
                if pat.count(PREFERRED_SAME) == m:
                    self.proportional_completion_round(pat, profile)

        try:
            assert round(weight_sum, 5) == round(sum(profile.values()), 5)
        except Exception:
            print(
                f"Proportional completion broke (went from {weight_sum} to {sum(profile.values())})"
            )

        return profile

    def proportional_completion_round(
        self, completion_pattern: tuple[int, ...], profile: dict[tuple[int, ...], float]
    ) -> dict[tuple[int, ...], float]:
        weight_sum = sum(profile.values())
        completion_pattern_weight = profile[completion_pattern]
        del profile[completion_pattern]

        patterns_to_consider: dict[tuple[int, ...], set[tuple[int, ...]]] = {}
        for pattern in list(profile.keys()):
            append = False
            append_target: list[int] = []
            for i in range(len(completion_pattern)):
                if completion_pattern[i] == PREFERRED_SAME:
                    append_target.append(pattern[i])
                    if pattern[i] != PREFERRED_SAME:
                        append = True
                else:
                    append_target.append(completion_pattern[i])

            if append is True:
                target = tuple(append_target)
                if target not in patterns_to_consider:
                    patterns_to_consider[target] = set()
                patterns_to_consider[target].add(pattern)

        denominator = 0.0
        for patterns in patterns_to_consider.values():
            for pattern in patterns:
                denominator += profile[pattern]

        for target_pattern, patterns in patterns_to_consider.items():
            if denominator == 0:
                profile[target_pattern] = profile.get(
                    target_pattern, 0.0
                ) + completion_pattern_weight / len(patterns_to_consider)
            else:
                if target_pattern not in profile:
                    profile[target_pattern] = 0.0
                profile[target_pattern] += (
                    sum(profile[p] for p in patterns) * completion_pattern_weight / denominator
                )

        try:
            assert round(weight_sum, 5) == round(sum(profile.values()), 5)
        except Exception:
            total = sum(profile.values())
            print(f"Proportional completion round broke (went from {weight_sum} to {total})")

        return profile

    def strength_of_vote_management(self, voter_profile: dict[tuple[int, ...], float]) -> float:
        for pattern in self.pattern_nodes:
            self.vote_management_graph.set_edge_weight(
                (NODE_SOURCE, pattern), voter_profile[pattern]
            )
            for i in range(self.required_winners):  # type: ignore[attr-defined]
                if pattern[i] == 1:
                    self.vote_management_graph.set_edge_weight((pattern, i), voter_profile[pattern])

        r = [
            (
                float(sum(voter_profile.values()))
                - voter_profile[tuple([PREFERRED_MORE] * self.required_winners)]
            )
            / self.required_winners
        ]  # type: ignore[attr-defined]
        while len(r) < 2 or r[-2] - r[-1] > STRENGTH_TOLERANCE:
            for i in range(self.required_winners):  # type: ignore[attr-defined]
                self.vote_management_graph.set_edge_weight((i, NODE_SINK), r[-1])
            max_flow = maximum_flow(self.vote_management_graph, NODE_SOURCE, NODE_SINK)
            sink_sum = sum(v for k, v in max_flow[0].items() if k[1] == NODE_SINK)
            r.append(sink_sum / self.required_winners)  # type: ignore[attr-defined]

            if sink_sum < STRENGTH_THRESHOLD:
                return 0.0

        return float(round(r[-1], 9))
