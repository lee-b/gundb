from typing import List
from .core_types import VectorClockType
from .site import Site
from .event_stream import EventStream
from .models import Event

class VectorClock:
    """
    Utility class for handling vector clocks.
    """
    @staticmethod
    def merge(clock1: VectorClockType, clock2: VectorClockType) -> VectorClockType:
        merged = clock1.copy()
        for key, value in clock2.items():
            if key in merged:
                merged[key] = max(merged[key], value)
            else:
                merged[key] = value
        return merged

    @staticmethod
    def increment(clock: VectorClockType, site: Site, stream: EventStream) -> VectorClockType:
        new_clock = clock.copy()
        key = str(site.id)
        new_clock[key] = new_clock.get(key, 0) + 1
        return new_clock

    @staticmethod
    def merge_and_increment(clock1: VectorClockType, clock2: VectorClockType, site: Site, stream: EventStream) -> VectorClockType:
        merged = VectorClock.merge(clock1, clock2)
        return VectorClock.increment(merged, site, stream)

    @staticmethod
    def _happened_before(vc1: VectorClockType, vc2: VectorClockType) -> bool:
        """
        Determines if vc1 happened before vc2.
        """
        less_or_equal = True
        strictly_less = False
        for key in set(vc1.keys()).union(vc2.keys()):
            v1 = vc1.get(key, 0)
            v2 = vc2.get(key, 0)
            if v1 > v2:
                less_or_equal = False
                break
            if v1 < v2:
                strictly_less = True
        return less_or_equal and strictly_less

    @staticmethod
    def _has_conflict(vc1: VectorClockType, vc2: VectorClockType) -> bool:
        """
        Determines if there is a conflict between two vector clocks that could indicate a cycle.
        A conflict is detected if neither clock happened before the other and
        each has at least one key with a strictly greater value than the other,
        indicating conflicting updates that cannot be resolved causally.
        """
        if VectorClock._happened_before(vc1, vc2) or VectorClock._happened_before(vc2, vc1):
            return False
        has_greater_in_vc1 = any(vc1.get(k, 0) > vc2.get(k, 0) for k in vc1)
        has_greater_in_vc2 = any(vc2.get(k, 0) > vc1.get(k, 0) for k in vc2)
        return has_greater_in_vc1 and has_greater_in_vc2

    @staticmethod
    def sort_events(events: List[Event]) -> List[Event]:
        """
        Sort events based on their vector clocks to respect causal dependencies.
        Implements a topological sort where edges represent 'happened-before' relationships.
        Concurrent events (no causal relationship) are rejected to enforce total ordering.
        """
        if not events:
            return []

        # Build a dependency graph based strictly on happened_before relationships
        n = len(events)
        graph = [[] for _ in range(n)]
        in_degree = [0] * n
        event_map = {event: i for i, event in enumerate(events)}

        for i in range(n):
            for j in range(n):
                if i != j:
                    if VectorClock._happened_before(events[i].vector_clock, events[j].vector_clock):
                        graph[i].append(j)
                        in_degree[j] += 1

        # Check for cycles using DFS based on happened_before relationships
        visited = set()
        rec_stack = set()

        def detect_cycle(node):
            visited.add(node)
            rec_stack.add(node)
            for neighbor in graph[node]:
                if neighbor not in visited:
                    if detect_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            rec_stack.remove(node)
            return False

        # Run cycle detection on all unvisited nodes
        cycle_detected = False
        for i in range(n):
            if i not in visited:
                if detect_cycle(i):
                    cycle_detected = True
                    break

        if cycle_detected:
            raise Exception("Cyclic dependencies detected in event vector clocks")

        # Perform topological sort using Kahn's algorithm
        queue = []
        for i in range(n):
            if in_degree[i] == 0:
                queue.append(i)

        sorted_indices = []
        while queue:
            node = queue.pop(0)
            sorted_indices.append(node)
            for neighbor in graph[node]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_indices) != n:
            raise Exception("Cyclic dependencies detected in event vector clocks")

        # Convert indices back to events
        result = [events[i] for i in sorted_indices]

        # Additional check for conflicting vector clocks that indicate concurrency or cycles
        for i in range(n):
            for j in range(n):
                if i != j and VectorClock._has_conflict(events[i].vector_clock, events[j].vector_clock):
                    # Check if this conflict could imply a cycle by examining if there are mutual dependencies
                    # A cycle in vector clocks is when conflicting clocks have values suggesting circular dependency
                    # For example, vc1: {A:1, B:2} and vc2: {A:2, B:1} suggest a cycle
                    conflict_keys = set(events[i].vector_clock.keys()).intersection(events[j].vector_clock.keys())
                    if conflict_keys:
                        cycle_suspected = True
                        for k in conflict_keys:
                            if not ((events[i].vector_clock[k] > events[j].vector_clock[k]) or (events[j].vector_clock[k] > events[i].vector_clock[k])):
                                cycle_suspected = False
                                break
                        if cycle_suspected:
                            raise Exception("Cyclic dependencies detected in event vector clocks")
                    raise Exception("Concurrent events detected; only causally ordered events are allowed in EventStreams")

        # For concurrent events (those not ordered by causality), sort by timestamp and ID
        final_result = []
        i = 0
        while i < len(result):
            start = i
            while i < len(result) - 1 and not VectorClock._happened_before(result[i].vector_clock, result[i + 1].vector_clock) and not VectorClock._happened_before(result[i + 1].vector_clock, result[i].vector_clock):
                i += 1
            if i > start:
                # Sort concurrent events by timestamp and ID
                concurrent = result[start:i + 1]
                concurrent.sort(key=lambda e: (e.timestamp, str(e.id)))
                final_result.extend(concurrent)
            else:
                final_result.append(result[start])
            i += 1

        return final_result
