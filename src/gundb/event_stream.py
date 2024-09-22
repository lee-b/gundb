import uuid
from typing import Dict, Any, List, Type
from sqlalchemy import Column, String, Integer, UUID
from sqlalchemy.orm import relationship, declarative_base
from pydantic import BaseModel
from .core_types import EventStreamUUID
from .site import Site
from .models import Event, View

Base = declarative_base()

def generate_uuid() -> uuid.UUID:
    """Generates a unique UUID."""
    return uuid.uuid4()

class EventStream(Base):
    """
    Base class for all Event Streams.
    Each stream type should inherit from this class and provide a unique UUID.
    """
    __tablename__ = 'event_streams'

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    name = Column(String, unique=True, nullable=False)
    event_counter = Column(Integer, default=0, nullable=False)
    latest_merged_event_counter = Column(Integer, default=0, nullable=False)

    # Relationships
    events = relationship("Event", back_populates="stream", cascade="all, delete-orphan")
    view = relationship("View", uselist=False, back_populates="stream", cascade="all, delete-orphan")

    def __init__(self, name: str, event_type: Type[BaseModel]):
        self.name = name
        self._event_type = event_type
        self.event_counter = 0
        self.latest_merged_event_counter = 0

    def update_with_events(self, events: List[Event], site: Site):
        """
        Update the stream with a list of events, correctly sorting them using vector clocks.
        """
        from .vector_clock import VectorClock
        sorted_events = VectorClock.sort_events(events)
        for event in sorted_events:
            self.apply_event(event, site)

    def apply_event(self, event: Event, site: Site):
        """
        Apply a single event to the stream and update the view.
        """
        from .vector_clock import VectorClock
        if not self.view:
            self.view = View(self.id)
        
        self.event_counter += 1
        event.position = self.event_counter
        
        self.view.apply_event(event)
        event.vector_clock = VectorClock.merge_and_increment(event.vector_clock, self.view.vector_clock, site, self)
        
        # Update the latest merged event counter
        self.latest_merged_event_counter = max(self.latest_merged_event_counter, event.position)

    def validate_data(self, data: Dict[str, Any]):
        """
        Validate the data against the Pydantic event type.
        """
        return self._event_type(**data)

    def get_type(self) -> Type[BaseModel]:
        """
        Return the Pydantic event type associated with this EventStream.
        """
        return self._event_type

    def get_schema(self) -> Dict[str, Any]:
        """
        Return the JSON schema of the Pydantic event type.
        """
        return self._event_type.schema()
