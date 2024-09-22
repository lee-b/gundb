from typing import Dict, Any, Type
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase
from .core_types import EventStreamUUID, VectorClockType, EventUUID
from .site import Site

class Base(DeclarativeBase):
    pass

class Event(Base):
    """
    Base class for all Events.
    Connected to an EventStream via foreign key.
    """
    def __init__(self, stream: 'EventStream', vector_clock: VectorClockType, data: BaseModel):
        self.id: EventUUID
        self.stream_id: EventStreamUUID
        self.vector_clock: VectorClockType = vector_clock
        self.data: Dict[str, Any] = data.dict()

class UserEvent(BaseModel):
    pass

class UserCreatedEvent(Event):
    pass

class UserUpdatedEvent(Event):
    pass
