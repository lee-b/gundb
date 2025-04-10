import pytest
from gundb.nodes import EventSourceNode, EventSinkNode
from gundb.models import Event, UserStream, UserEvent, UserCreatedEvent
from gundb.site import Site

class MockEventSourceNode(EventSourceNode):
    def send_event(self, event: Event):
        pass

class MockEventSinkNode(EventSinkNode):
    def __init__(self):
        self.received_events = []

    def receive_event(self, event: Event):
        self.received_events.append(event)

@pytest.fixture
def mock_nodes():
    source = MockEventSourceNode()
    sink = MockEventSinkNode()
    return source, sink

def test_event_source_node(mock_nodes):
    source, sink = mock_nodes
    user_stream = UserStream()
    event = UserCreatedEvent(stream=user_stream, vector_clock={}, data=UserEvent(username="test_user", email="test@example.com", age=30))
    
    # Simulate sending an event
    source.send_event(event)
    # Here, we would typically check if the event was sent correctly, but since send_event is a mock, we'll just ensure it doesn't raise an exception

def test_event_sink_node(mock_nodes):
    source, sink = mock_nodes
    user_stream = UserStream()
    event = UserCreatedEvent(stream=user_stream, vector_clock={}, data=UserEvent(username="test_user", email="test@example.com", age=30))
    
    # Send an event to the sink node
    sink.receive_event(event)
    
    # Check if the event was received
    assert len(sink.received_events) == 1
    assert sink.received_events[0] == event

def test_node_interaction(mock_nodes):
    source, sink = mock_nodes
    user_stream = UserStream()
    event = UserCreatedEvent(stream=user_stream, vector_clock={}, data=UserEvent(username="test_user", email="test@example.com", age=30))
    
    # Simulate sending an event from source to sink
    source.send_event(event)
    sink.receive_event(event)
    
    # Check if the event was received by the sink
    assert len(sink.received_events) == 1
    assert sink.received_events[0] == event

if __name__ == "__main__":
    pytest.main()
