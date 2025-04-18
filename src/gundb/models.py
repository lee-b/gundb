from typing import Dict, Any, Optional, List
from pydantic import BaseModel
from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid
from .base import Base
from .core_types import EventStreamUUID, VectorClockType, SiteUUID
from .events import UserEvent, UserCreatedEvent, UserUpdatedEvent
from .event_stream import EventStream
from .event import Event
from .site import Site
from .utils import generate_uuid

class View(Base):
    """
    Represents the current state of a stream, updated with events.
    """
    __tablename__ = 'views'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    stream_id = Column(UUID(as_uuid=True), nullable=False)
    snapshot = Column(JSON, nullable=True)
    vector_clock = Column(JSON, nullable=True)

    def __init__(self, stream_id: EventStreamUUID, snapshot: Optional[Dict[str, Any]] = None, vector_clock: Optional[VectorClockType] = None):
        self.stream_id = stream_id
        self.snapshot = snapshot or {}
        self.vector_clock = vector_clock or {}

    def apply_event(self, event: Event):
        # Update the snapshot based on the event
        if isinstance(event.data, dict):
            self.snapshot.update(event.data)
        else:
            # Convert non-dict data to dict if possible
            try:
                self.snapshot = event.data.model_dump()
            except (TypeError, ValueError, AttributeError):
                self.snapshot = {}
        
        # Update the vector clock
        for site, timestamp in event.vector_clock.items():
            site_str = str(site)
            try:
                current_val = int(self.vector_clock.get(site_str, 0))
                new_val = int(timestamp) if isinstance(timestamp, (int, str)) else 0
                self.vector_clock[site_str] = max(current_val, new_val)
            except (ValueError, TypeError):
                # If timestamp is not convertible to int, use it as is (for string IDs)
                self.vector_clock[site_str] = timestamp

class UserStream(EventStream):
    __mapper_args__ = {
        'polymorphic_identity': 'user_stream',
    }

    def __init__(self, name: str = "user_stream"):
        super().__init__(name, UserEvent)
        self.view = View(stream_id=self.id)
        self.latest_merged_event_counter = 0

    def apply_event(self, event: Event, site: Site):
        """
        Apply an event to the stream, incrementing the event counter.
        Additional behavior can be added in derived classes' overridden implementations.
        """
        # Validate vector clock keys to ensure they are valid site IDs or stream IDs
        for key in event.vector_clock.keys():
            try:
                uuid.UUID(str(key))  # Check if key is a valid UUID string
            except (ValueError, TypeError):
                raise ValueError(f"Invalid vector clock key: {key}. Must be a valid UUID string.")
                
        self.event_counter += 1
        # Update latest_merged_event_counter based on event position if available
        if hasattr(event, 'position') and event.position is not None:
            self.latest_merged_event_counter = max(self.latest_merged_event_counter, event.position)
        else:
            self.latest_merged_event_counter += 1
        self.view.apply_event(event)
        # Update vector clock with site information
        site_id = SiteUUID(site.site_id) if hasattr(site, 'site_id') else SiteUUID(uuid.uuid4())
        self.view.vector_clock[str(self.id)] = str(event.id)
