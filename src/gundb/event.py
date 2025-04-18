from typing import Dict, Any, Type
from pydantic import BaseModel
from sqlalchemy import Column, ForeignKey, JSON, Integer, DateTime, String
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .base import Base
from .core_types import EventStreamUUID, VectorClockType, EventUUID
from .site import Site
from .utils import generate_uuid
from datetime import datetime

class Event(Base):
    __tablename__ = 'events'

    id = Column(UUID(as_uuid=True), primary_key=True, default=generate_uuid)
    stream_id = Column(UUID(as_uuid=True), ForeignKey('event_streams.id'), nullable=False)
    vector_clock = Column(JSON, nullable=False)
    data = Column(JSON, nullable=False)
    position = Column(Integer, default=1)
    timestamp = Column(DateTime, default=datetime.utcnow)
    type = Column(String, nullable=False)

    def __init__(self, stream, vector_clock: VectorClockType, data: BaseModel):
        self.stream_id = stream.id
        self.vector_clock = vector_clock
        self.data = data.model_dump()
        self.type = self.__class__.__name__
