from typing import Dict, Any, Type, List
import uuid
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase
from .core_types import EventStreamUUID
from .site import Site
from .events import Event  # Add this import

class Base(DeclarativeBase):
    pass

class EventStream(Base):
    """
    Base class for all Event Streams.
    Each stream type should inherit from this class and provide a unique UUID.
    """
    def __init__(self, name: str, event_type: Type[BaseModel]):
        self.id: EventStreamUUID = EventStreamUUID(uuid.uuid4())
        self.name: str = name
        self._event_type: Type[BaseModel] = event_type

    def update_with_events(self, events: List[Event], site: Site):
        for event in events:
            self.apply_event(event, site)

    def apply_event(self, event: Event, site: Site):
        # This method should be implemented by subclasses
        raise NotImplementedError

    def validate_data(self, data: Dict[str, Any]):
        return self._event_type(**data)

    def get_type(self) -> Type[BaseModel]:
        return self._event_type

    def get_schema(self) -> Dict[str, Any]:
        return self._event_type.schema()

def generate_uuid() -> uuid.UUID:
    return uuid.uuid4()
