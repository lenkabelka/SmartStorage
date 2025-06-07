from PyQt6.QtGui import QImage
from PyQt6.QtWidgets import QMessageBox
from dataclasses import dataclass, field
from typing import Optional
#from projection import Projection
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

    #projections: list[Optional["Projection"]] = field(default_factory=list) # DB

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

    def insert(self):
        query = """
            INSERT INTO spaces.things (thing_name, thing_description, thing_image, id_parent_space)
            VALUES (%s, %s, %s, %s)
            RETURNING id_thing;
        """
        image_bytes = utils.qimage_to_bytes(self.image) if self.image else None
        values = (self.name, self.description, image_bytes, self.id_parent_space)
        conn = None
        try:
            config = connection.load_config()
            conn = connection.db_connect(config)
            with conn:
                with conn.cursor() as cur:
                    cur.execute(query, values)
                    self.id_thing = cur.fetchone()[0]
                    self.show_message("Успешно", f"Вещь добавлена с ID: {self.id_thing}")
                    self.reset_state()
                    return self.id_thing
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            self.show_message("Ошибка при вставке", str(e), icon=QMessageBox.Icon.Critical)
        finally:
            if conn:
                conn.close()

    def update(self):
        if self.id_thing is None:
            self.show_message("Ошибка", "Невозможно обновить: id_thing отсутствует", icon=QMessageBox.Icon.Warning)
            return
        query = """
            UPDATE spaces.things
            SET thing_name = %s, thing_description = %s, thing_image = %s
            WHERE id_thing = %s
        """
        image_bytes = utils.qimage_to_bytes(self.image) if self.image else None
        values = (self.name, self.description, image_bytes, self.id_thing)
        conn = None
        try:
            config = connection.load_config()
            conn = connection.db_connect(config)
            with conn:
                with conn.cursor() as cur:
                    cur.execute(query, values)
                    self.show_message("Успешно", f"Вещь с ID {self.id_thing} обновлена")
                    self.reset_state()
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            self.show_message("Ошибка при обновлении", str(e), icon=QMessageBox.Icon.Critical)
        finally:
            if conn:
                conn.close()


    def delete(self):
        if self.id_thing is None:
            self.show_message("Ошибка", "Невозможно удалить: id_thing отсутствует", icon=QMessageBox.Icon.Warning)
            return
        query = "DELETE FROM spaces.things WHERE id_thing = %s"
        values = (self.id_thing,)
        conn = None
        try:
            config = connection.load_config()
            conn = connection.db_connect(config)
            with conn:
                with conn.cursor() as cur:
                    cur.execute(query, values)
                    self.show_message("Успешно", f"Вещь с ID {self.id_thing} удалена")
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            self.show_message("Ошибка при удалении", str(e), icon=QMessageBox.Icon.Critical)
        finally:
            if conn:
                conn.close()


    # def save_thing(self, space_projections):
    #     self.save()
    #     print(f"id_thing: {self.id_thing}")
    #
    #     if self.projections:
    #         for projection in self.projections:
    #             if not projection.id_parent_thing:
    #                 projection.id_parent_thing = self.id_thing
    #
    #             parent_projection = next(
    #                 (pr for pr in space_projections if projection.reference_to_parent_projection == pr), None)
    #             print(f"parent_projection: {parent_projection}")
    #             if parent_projection:
    #                 projection.id_parent_projection = parent_projection.id_projection
    #                 print(f"projection.id_projection: {projection.id_parent_projection}")
    #
    #             projection.save()