from datetime import datetime, timedelta

import pytest

from gundb.models import Event
from gundb.vector_clock import VectorClock
from gundb.site import Site
from gundb.event_stream import EventStream


def create_mock_event(event_id, vector_clock, timestamp):
    """Helper function to create mock events."""
    site = Site()
    stream = EventStream("test_stream", Event)
    event = Event(
        stream=stream,
        vector_clock=vector_clock,
        data={"key": "value"}
    )
    event.id = event_id
    event.timestamp = timestamp
    return event

def test_sort_events_linear_causality():
    # Create mock events with linear causality
    event1 = create_mock_event("1", {"A":1}, datetime.now())
    event2 = create_mock_event("2", {"A":2}, datetime.now() + timedelta(seconds=1))
    event3 = create_mock_event("3", {"A":3}, datetime.now() + timedelta(seconds=2))

    events = [event3, event1, event2]
    sorted_events = VectorClock.sort_events(events)

    assert [e.id for e in sorted_events] == ["1", "2", "3"]

def test_sort_events_branching_causality():
    # Create mock events with branching causality
    event1 = create_mock_event("1", {"A":1}, datetime.now())
    event2 = create_mock_event("2", {"A":1, "B":1}, datetime.now() + timedelta(seconds=1))
    event3 = create_mock_event("3", {"A":1, "B":2}, datetime.now() + timedelta(seconds=2))
    event4 = create_mock_event("4", {"A":2, "B":2}, datetime.now() + timedelta(seconds=3))

    events = [event4, event2, event3, event1]
    sorted_events = VectorClock.sort_events(events)

    assert [e.id for e in sorted_events] == ["1", "2", "3", "4"]

def test_sort_events_concurrent_events():
    # Create mock concurrent events
    event1 = create_mock_event("1", {"A":1}, datetime.now())
    event2 = create_mock_event("2", {"B":1}, datetime.now() + timedelta(seconds=1))
    event3 = create_mock_event("3", {"A":1, "B":1}, datetime.now() + timedelta(seconds=2))

    events = [event2, event1, event3]
    sorted_events = VectorClock.sort_events(events)

    # event1 and event2 are concurrent; sorted by timestamp then id
    assert [e.id for e in sorted_events] == ["1", "2", "3"]

def test_sort_events_cycle_detection():
    # Create mock events with cyclic dependencies (invalid vector clocks)
    event1 = create_mock_event("1", {"A":1, "B":1}, datetime.now())
    event2 = create_mock_event("2", {"A":1, "B":1}, datetime.now() + timedelta(seconds=1))

    # Manually create a cycle by setting event1 to depend on event2 and vice versa
    # Normally, vector clocks should prevent this, but for testing:
    event1.vector_clock = {"A":1, "B":2}
    event2.vector_clock = {"A":2, "B":1}

    events = [event1, event2]

    with pytest.raises(Exception) as exc_info:
        VectorClock.sort_events(events)
    
    assert "Cyclic dependencies detected" in str(exc_info.value)
