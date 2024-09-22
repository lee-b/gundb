import uuid
from typing import Optional

class Site:
    """
    Represents a unique site in the distributed system.
    """
    def __init__(self, site_id: Optional[str] = None):
        self.id = site_id or str(uuid.uuid4())

    def __str__(self):
        return f"Site({self.id})"

    def __repr__(self):
        return self.__str__()
