from abc import ABC, abstractmethod
from .models import Event

class EventSourceNode(ABC):
    """
    Abstract base class for nodes that send events.
    """
    @abstractmethod
    def send_event(self, event: Event):
        """Send an event to other nodes."""
        pass

class EventSinkNode(ABC):
    """
    Abstract base class for nodes that receive events.
    """
    @abstractmethod
    def receive_event(self, event: Event):
        """Receive an event from other nodes."""
        pass
