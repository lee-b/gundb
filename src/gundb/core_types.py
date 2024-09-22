from typing import Dict, Any, NewType
import uuid

# UUID types
EventStreamUUID = NewType('EventStreamUUID', uuid.UUID)
SiteUUID = NewType('SiteUUID', uuid.UUID)
EventUUID = NewType('EventUUID', uuid.UUID)

# Vector clock type
VectorClockType = Dict[SiteUUID, int]

# Generic data type
DataType = Dict[str, Any]
