from PyQt6.QtGui import QImage
from dataclasses import dataclass, field
from typing import Optional
import projection
import track_object_state
import image as im
import connect_DB as connection
import psycopg2
import space


from track_object_state import ObjectState


@dataclass
class Thing(track_object_state.Trackable):
    name: str  # DB

    reference_to_parent_space: Optional["space.Space"]

    description: str = None  # DB
    image: QImage = None # DB

    projections: list[projection.Projection] = field(default_factory=list) # DB

    id_thing: Optional[int] = None  # DB
    id_parent_space: Optional[int] = None  # DB


    def __post_init__(self):
        self._db_fields = {'id_thing', 'name', 'description'}
        super().__post_init__()


    def insert(self):
        pass


    def update(self):
        pass


    def delete(self):
        pass