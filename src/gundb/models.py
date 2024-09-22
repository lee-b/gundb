import uuid
from typing import Dict, Any, Optional, List, Tuple
from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    DateTime,
    JSON,
    create_engine,
    event as sqlalchemy_event,
)
from sqlalchemy.orm import (
    declarative_base,
    relationship,
)
from sqlalchemy.sql import func
from .vector_clock import VectorClock
from .site import Site

Base = declarative_base()

def generate_uuid() -> str:
    """Generates a unique UUID string."""
    return str(uuid.uuid4())

class EventStream(Base):
    """
    Base class for all Event Streams.
    Each stream type should inherit from this class and provide a unique UUID.
    """
    __tablename__ = 'event_streams'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String, unique=True, nullable=False)

    # Relationships
    events = relationship("Event", back_populates="stream", cascade="all, delete-orphan")
    view = relationship("View", uselist=False, back_populates="stream", cascade="all, delete-orphan")

    def __init__(self, name: str):
        self.name = name

    def update_with_events(self, events: List['Event'], site: Site):
        """
        Update the stream with a list of events, correctly sorting them using vector clocks.
        """
        sorted_events = VectorClock.sort_events(events)
        for event in sorted_events:
            self.apply_event(event, site)

    def apply_event(self, event: 'Event', site: Site):
        """
        Apply a single event to the stream and update the view.
        """
        if not self.view:
            self.view = View(self.id)
        
        self.view.apply_event(event)
        event.vector_clock = VectorClock.merge_and_increment(event.vector_clock, self.view.vector_clock, site, self)

class Event(Base):
    """
    Base class for all Events.
    Connected to an EventStream via foreign key.
    """
    __tablename__ = 'events'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    stream_id = Column(String(36), ForeignKey('event_streams.id'), nullable=False)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    vector_clock = Column(JSON, nullable=False, default=dict)
    type = Column(String, nullable=False)

    # To store event data as key-value pairs
    data = Column(JSON, nullable=True)

    # Relationships
    stream = relationship("EventStream", back_populates="events")

    __mapper_args__ = {
        'polymorphic_identity': 'event',
        'polymorphic_on': type
    }

    def __init__(self, stream_id: str, site: Site, vector_clock: Optional[Dict[Tuple[str, str], int]] = None, data: Optional[Dict[str, Any]] = None):
        self.stream_id = stream_id
        self.vector_clock = vector_clock or {}
        self.data = data or {}
        if not vector_clock:
            self.vector_clock = {(site.id, stream_id): 1}

class View(Base):
    """
    Represents the current state of a stream, updated with events.
    """
    __tablename__ = 'views'

    id = Column(String(36), primary_key=True, default=generate_uuid)
    stream_id = Column(String(36), ForeignKey('event_streams.id'), unique=True, nullable=False)
    snapshot = Column(JSON, nullable=True, default=dict)
    vector_clock = Column(JSON, nullable=False, default=dict)

    # Relationships
    stream = relationship("EventStream", back_populates="view")

    def __init__(self, stream_id: str, snapshot: Optional[Dict[str, Any]] = None, vector_clock: Optional[Dict[Tuple[str, str], int]] = None):
        self.stream_id = stream_id
        self.snapshot = snapshot or {}
        self.vector_clock = vector_clock or {}

    def apply_event(self, event: 'Event'):
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
        self.vector_clock = VectorClock.merge(self.vector_clock, event.vector_clock)

# Example of a specific EventStream
class UserStream(EventStream):
    __mapper_args__ = {
        'polymorphic_identity': 'user_stream',
    }

    def __init__(self, name: str = "user_stream"):
        super().__init__(name)

# Example of specific Events
class UserCreatedEvent(Event):
    __mapper_args__ = {
        'polymorphic_identity': 'user_created',
    }

    def __init__(self, stream_id: str, site: Site, vector_clock: Optional[Dict[Tuple[str, str], int]] = None, data: Optional[Dict[str, Any]] = None):
        super().__init__(stream_id, site, vector_clock, data)

class UserUpdatedEvent(Event):
    __mapper_args__ = {
        'polymorphic_identity': 'user_updated',
    }

    def __init__(self, stream_id: str, site: Site, vector_clock: Optional[Dict[Tuple[str, str], int]] = None, data: Optional[Dict[str, Any]] = None):
        super().__init__(stream_id, site, vector_clock, data)
