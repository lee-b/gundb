import uuid
from typing import Dict, Any, Optional, List, Iterator
from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    DateTime,
    JSON,
    Integer,
    create_engine,
    event as sqlalchemy_event,
)
from sqlalchemy.orm import (
    relationship,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from pydantic import BaseModel
from .core_types import SiteUUID, EventStreamUUID, VectorClockType
from .site import Site
from .event_stream import EventStream, Base

def generate_uuid() -> uuid.UUID:
    """Generates a unique UUID."""
    return uuid.uuid4()

class Event(Base):
    """
    Base class for all Events.
    Connected to an EventStream via foreign key.
    """
    __tablename__ = 'events'

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    stream_id = Column(UUID(as_uuid=True), ForeignKey('event_streams.id'), nullable=False)
    position = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    vector_clock = Column(JSON, nullable=False)
    type = Column(String, nullable=False)

    # To store event data as JSON
    data = Column(JSON, nullable=False)

    # Relationships
    stream = relationship("EventStream", back_populates="events")

    __mapper_args__ = {
        'polymorphic_identity': 'event',
        'polymorphic_on': type
    }

    def __init__(self, stream: EventStream, vector_clock: VectorClockType, data: BaseModel):
        self.id = generate_uuid()
        self.stream_id = stream.id
        self.vector_clock = {str(self.stream_id): str(self.id)}
        self.data = data.dict()
        self.type = self.__class__.__name__
        # The position will be set when the event is applied to the stream

    @classmethod
    def events_as_vector_clock(cls, events: Iterator['Event']) -> VectorClockType:
        """
        Convert a sequence of events into a single VectorClock.
        """
        from .vector_clock import VectorClock
        combined_clock = {}
        for event in events:
            combined_clock = VectorClock.merge(combined_clock, event.vector_clock)
        return combined_clock

class View(Base):
    """
    Represents the current state of a stream, updated with events.
    """
    __tablename__ = 'views'

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    stream_id = Column(UUID(as_uuid=True), ForeignKey('event_streams.id'), unique=True, nullable=False)
    snapshot = Column(JSON, nullable=True, default=dict)
    vector_clock = Column(JSON, nullable=False, default=dict)

    # Relationships
    stream = relationship("EventStream", back_populates="view")

    def __init__(self, stream_id: EventStreamUUID, snapshot: Optional[Dict[str, Any]] = None, vector_clock: Optional[VectorClockType] = None):
        self.stream_id = stream_id
        self.snapshot = snapshot or {}
        self.vector_clock = vector_clock or {}

    def apply_event(self, event: Event):
        """
        Apply an event to update the snapshot and vector clock.
        """
        if event.data:
            for key, value in event.data.items():
                if value is not None:
                    self.snapshot[key] = value
                else:
                    self.snapshot.pop(key, None)
        
        # Update vector clock
        from .vector_clock import VectorClock
        self.vector_clock = VectorClock.merge(self.vector_clock, event.vector_clock)

# Example of a specific EventStream with Pydantic event type
class UserEvent(BaseModel):
    username: str
    email: str
    age: int

class UserStream(EventStream):
    __mapper_args__ = {
        'polymorphic_identity': 'user_stream',
    }

    def __init__(self, name: str = "user_stream"):
        super().__init__(name, UserEvent)

# Example of specific Events
class UserCreatedEvent(Event):
    __mapper_args__ = {
        'polymorphic_identity': 'user_created',
    }

class UserUpdatedEvent(Event):
    __mapper_args__ = {
        'polymorphic_identity': 'user_updated',
    }
