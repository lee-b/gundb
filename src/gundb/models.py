from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase
from .core_types import EventStreamUUID, VectorClockType
from .events import Event, UserEvent, UserCreatedEvent, UserUpdatedEvent
from .event_stream import EventStream, Base

class View(Base):
    """
    Represents the current state of a stream, updated with events.
    """
    def __init__(self, stream_id: EventStreamUUID, snapshot: Optional[Dict[str, Any]] = None, vector_clock: Optional[VectorClockType] = None):
        self.stream_id: EventStreamUUID = stream_id
        self.snapshot: Dict[str, Any] = snapshot or {}
        self.vector_clock: VectorClockType = vector_clock or {}

    def apply_event(self, event: Event):
        # Update the snapshot based on the event
        self.snapshot.update(event.data)
        
        # Update the vector clock
        for site, timestamp in event.vector_clock.items():
            self.vector_clock[site] = max(self.vector_clock.get(site, 0), timestamp)

class UserStream(EventStream):
    __mapper_args__ = {
        'polymorphic_identity': 'user_stream',
    }

    def __init__(self, name: str = "user_stream"):
        super().__init__(name, UserEvent)
