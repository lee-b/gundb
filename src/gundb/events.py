from pydantic import BaseModel, Field, ValidationError
from typing import Dict, Any, Optional
from .event_stream import EventStream
from .event import Event
from .core_types import VectorClockType

class UserEvent(BaseModel):
    """
    Base class for user-defined events in the SDK.
    SDK users can inherit from this class to implement custom event types.
    """
    username: str
    email: str
    age: int

class UserCreatedEvent(Event):
    def __init__(self, stream: EventStream, vector_clock: VectorClockType, data: UserEvent):
        super().__init__(stream=stream, vector_clock=vector_clock, data=data)

class UserUpdatedEvent(Event):
    def __init__(self, stream: EventStream, vector_clock: VectorClockType, data: UserEvent):
        super().__init__(stream=stream, vector_clock=vector_clock, data=data)
