import uuid
from typing import Optional, NewType

SiteUUID = NewType('SiteUUID', uuid.UUID)

class Site:
    """
    Represents a unique site in the distributed system.
    """
    def __init__(self, site_id: Optional[SiteUUID] = None):
        self.id: SiteUUID = site_id or SiteUUID(uuid.uuid4())

    def __str__(self):
        return f"Site({self.id})"

    def __repr__(self):
        return self.__str__()
