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
        key = (str(site.id), str(stream.id))
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
    def sort_events(events: List[Event]) -> List[Event]:
        """
        Sort events based on their vector clocks to respect causal dependencies.
        Implements a topological sort where edges represent 'happened-before' relationships.
        Concurrent events (no causal relationship) are sorted by timestamp, then by UUID.
        """
        # Implementation remains the same as before
        # ...
