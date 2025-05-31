from dataclasses import dataclass, field
from typing import Optional
import psycopg2

from PyQt6.QtGui import QPixmap
import track_object_state
import queries_for_DB as q


@dataclass
class SpaceImage(track_object_state.Trackable):
    image: QPixmap # DB
    name: str = None  # DB
    id_image: Optional[int] = None  # DB
    id_parent_space: int = None # DB

    def __post_init__(self):
        self._db_fields = {'id_image', 'name', 'image', 'id_parent_space'}
        super().__post_init__()


    def insert_image_to_DB(self):
        query = """
            INSERT INTO spaces.images (id_parent_space, image, image_name)
            VALUES (%s, %s, %s)
            RETURNING id_image;
        """
        values = (self.id_parent_space, self.image, self.name)

        conn = None
        try:
            config = q.load_config()
            conn = q.db_connect(config)
            with conn:
                with conn.cursor() as cur:
                    cur.execute(query, values)
                    print("saved_DB")
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            print("Error by insert:", e)
        finally:
            if conn:
                conn.close()