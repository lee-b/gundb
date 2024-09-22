from typing import Dict, Any, List, Optional, Set
from .models import Event
from collections import defaultdict, deque


class VectorClock:
    """
    Utility class for handling vector clocks.
    """
    def __init__(self, clock: Optional[Dict[str, int]] = None):
        self.clock = clock or {}

    def update(self, stream_id: str, counter: int):
        self.clock[stream_id] = max(self.clock.get(stream_id, 0), counter)

    def increment(self, stream_id: str):
        self.clock[stream_id] = self.clock.get(stream_id, 0) + 1

    def merge(self, other: 'VectorClock'):
        for stream_id, counter in other.clock.items():
            self.clock[stream_id] = max(self.clock.get(stream_id, 0), counter)

    def to_dict(self) -> Dict[str, int]:
        return self.clock

    @staticmethod
    def _happened_before(vc1: Dict[str, int], vc2: Dict[str, int]) -> bool:
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
    def sort_events(events: List[Event]) -> List[Event]:
        """
        Sort events based on their vector clocks to respect causal dependencies.
        Implements a topological sort where edges represent 'happened-before' relationships.
        Concurrent events (no causal relationship) are sorted by timestamp, then by UUID.
        """
        # Initialize adjacency list and in-degree count
        adjacency: Dict[str, Set[str]] = defaultdict(set)
        in_degree: Dict[str, int] = defaultdict(int)
        event_map: Dict[str, Event] = {event.id: event for event in events}

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
