from typing import Dict, Any, List, Optional, Set, Tuple
from collections import defaultdict, deque
from .site import Site

class VectorClock:
    """
    Utility class for handling vector clocks.
    """
    @staticmethod
    def merge(clock1: Dict[Tuple[str, str], int], clock2: Dict[Tuple[str, str], int]) -> Dict[Tuple[str, str], int]:
        merged = clock1.copy()
        for key, value in clock2.items():
            if key in merged:
                merged[key] = max(merged[key], value)
            else:
                merged[key] = value
        return merged

    @staticmethod
    def increment(clock: Dict[Tuple[str, str], int], site: Site, stream_id: str) -> Dict[Tuple[str, str], int]:
        new_clock = clock.copy()
        key = (site.id, stream_id)
        new_clock[key] = new_clock.get(key, 0) + 1
        return new_clock

    @staticmethod
    def merge_and_increment(clock1: Dict[Tuple[str, str], int], clock2: Dict[Tuple[str, str], int], site: Site, stream_id: str) -> Dict[Tuple[str, str], int]:
        merged = VectorClock.merge(clock1, clock2)
        return VectorClock.increment(merged, site, stream_id)

    @staticmethod
    def _happened_before(vc1: Dict[Tuple[str, str], int], vc2: Dict[Tuple[str, str], int]) -> bool:
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
    def sort_events(events: List['Event']) -> List['Event']:
        """
        Sort events based on their vector clocks to respect causal dependencies.
        Implements a topological sort where edges represent 'happened-before' relationships.
        Concurrent events (no causal relationship) are sorted by timestamp, then by UUID.
        """
        # Initialize adjacency list and in-degree count
        adjacency: Dict[str, Set[str]] = defaultdict(set)
        in_degree: Dict[str, int] = defaultdict(int)
        event_map: Dict[str, 'Event'] = {event.id: event for event in events}

        # Determine dependencies
        for event_a in events:
            for event_b in events:
                if event_a.id == event_b.id:
                    continue
                if VectorClock._happened_before(event_a.vector_clock, event_b.vector_clock):
                    if event_b.id not in adjacency[event_a.id]:
                        adjacency[event_a.id].add(event_b.id)
                        in_degree[event_b.id] += 1

        # Initialize queue with events having in-degree 0
        queue = deque([event_id for event_id in event_map if in_degree[event_id] == 0])

        sorted_event_ids: List[str] = []
        while queue:
            # To ensure deterministic ordering, sort the queue based on timestamp and UUID
            current_ids = list(queue)
            current_ids.sort(key=lambda eid: (event_map[eid].timestamp, eid))
            current_id = current_ids[0]
            queue.remove(current_id)

            sorted_event_ids.append(current_id)

            for neighbor in adjacency[current_id]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        if len(sorted_event_ids) != len(events):
            raise Exception("Cyclic dependencies detected among events.")

        # Return events sorted by sorted_event_ids
        sorted_events = [event_map[event_id] for event_id in sorted_event_ids]
        return sorted_events
