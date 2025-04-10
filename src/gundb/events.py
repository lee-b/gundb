from typing import Dict, Any, Type
from pydantic import BaseModel
from sqlalchemy.orm import DeclarativeBase
from .core_types import EventStreamUUID, VectorClockType, EventUUID
from .site import Site
from .event_stream import EventStream
from .event import Event

class Base(DeclarativeBase):
    pass

class UserEvent(BaseModel):
    pass

class UserCreatedEvent(Event):
    pass

class UserUpdatedEvent(Event):
    pass
