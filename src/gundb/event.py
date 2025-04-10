from typing import Dict, Any, Type
from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, JSON
from .base import Base
from .core_types import EventStreamUUID, VectorClockType, EventUUID
from .site import Site

class Event(Base):
    __tablename__ = 'events'

    id = Column(EventUUID, primary_key=True, default=generate_uuid)
    stream_id = Column(EventStreamUUID, ForeignKey('event_streams.id'), nullable=False)
    vector_clock = Column(JSON, nullable=False)
    data = Column(JSON, nullable=False)

    def __init__(self, stream, vector_clock: VectorClockType, data: BaseModel):
        self.stream_id = stream.id
        self.vector_clock = vector_clock
        self.data = data.dict()

