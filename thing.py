from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QMessageBox
from dataclasses import dataclass, field
from typing import Optional
import track_object_state
import image as im
import connect_DB as connection
import psycopg2
import utils


@dataclass
class Thing(track_object_state.Trackable):
    name: str  # DB

    reference_to_parent_space: Optional["Space"]

    description: str = None  # DB
    image: QImage = None # DB
    id_thing: Optional[int] = None  # DB
    id_parent_space: Optional[int] = None  # DB


    def __post_init__(self):
        self._db_fields = {'id_thing', 'name', 'description'}
        super().__post_init__()


    def show_message(self, title: str, message: str, icon=QMessageBox.Icon.Information):
        msg = QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setIcon(icon)
        msg.exec()


    def insert(self, cursor):
        query = """
            INSERT INTO spaces.things (thing_name, thing_description, thing_image, id_parent_space)
            VALUES (%s, %s, %s, %s)
            RETURNING id_thing;
        """
        image_bytes = utils.qimage_to_bytes(self.image) if self.image else None
        values = (self.name, self.description, image_bytes, self.id_parent_space)
        cursor.execute(query, values)
        self.id_thing = cursor.fetchone()[0]
        self.reset_state()
        print(f"Вещь добавлена с ID: {self.id_thing}")


    def update(self, cursor):
        if self.id_thing is None:
            raise ValueError("Невозможно обновить: id_thing отсутствует")

        query = """
            UPDATE spaces.things
            SET thing_name = %s, thing_description = %s, thing_image = %s
            WHERE id_thing = %s
        """
        image_bytes = utils.qimage_to_bytes(self.image) if self.image else None
        values = (self.name, self.description, image_bytes, self.id_thing)
        cursor.execute(query, values)
        self.reset_state()
        print(f"Вещь с ID {self.id_thing} обновлена")


    def delete(self, cursor):
        if self.id_thing is None:
            raise ValueError("Невозможно удалить: id_thing отсутствует")

        query = "DELETE FROM spaces.things WHERE id_thing = %s"
        values = (self.id_thing,)
        cursor.execute(query, values)
        print(f"Вещь с ID {self.id_thing} удалена")