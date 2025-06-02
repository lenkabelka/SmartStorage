from PyQt6.QtWidgets import QMessageBox
from dataclasses import dataclass, field
from PyQt6.QtCore import QByteArray, QBuffer, QIODevice
from PyQt6.QtGui import QPixmap
import psycopg2
import connect_DB as connection
from typing import Optional
import track_object_state
import utils as utils


@dataclass
class SpaceImage(track_object_state.Trackable):
    image: QPixmap  # DB
    name: str = None  # DB
    id_image: Optional[int] = None  # DB
    id_parent_space: int = None  # DB

    def __post_init__(self):
        self._db_fields = {'id_image', 'name', 'image', 'id_parent_space'}
        super().__post_init__()

    def show_message(self, title: str, message: str, icon=QMessageBox.Icon.Information):
        msg = QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setIcon(icon)
        msg.exec()


    def insert(self):
        query = """
            INSERT INTO spaces.images (id_parent_space, image, image_name)
            VALUES (%s, %s, %s)
            RETURNING id_image;
        """
        image_bytes = psycopg2.Binary(utils.pixmap_to_bytes(self.image))
        values = (self.id_parent_space, image_bytes, self.name)

        conn = None
        try:
            config = connection.load_config()
            conn = connection.db_connect(config)
            with conn:
                with conn.cursor() as cur:
                    cur.execute(query, values)
                    self.id_image = cur.fetchone()[0]
                    self.show_message("Успешно", f"Изображение добавлено с ID: {self.id_image}")
                    self.reset_state()
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            self.show_message("Ошибка при вставке", str(e), icon=QMessageBox.Icon.Critical)
        finally:
            if conn:
                conn.close()

    def update(self):
        if self.id_image is None:
            self.show_message("Ошибка", "Невозможно обновить: id_image отсутствует", icon=QMessageBox.Icon.Warning)
            return

        query = """
            UPDATE spaces.images
            SET image_name = %s, image = %s
            WHERE id_image = %s;
        """
        image_bytes = psycopg2.Binary(utils.pixmap_to_bytes(self.image))
        values = (self.name, image_bytes, self.id_image)

        conn = None
        try:
            config = connection.load_config()
            conn = connection.db_connect(config)
            with conn:
                with conn.cursor() as cur:
                    cur.execute(query, values)
                    self.show_message("Успешно", f"Изображение с ID {self.id_image} обновлено")
                    self.reset_state()
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            self.show_message("Ошибка при обновлении", str(e), icon=QMessageBox.Icon.Critical)
        finally:
            if conn:
                conn.close()


    def delete(self):
        if self.id_image is None:
            self.show_message("Ошибка", "Невозможно удалить: id_image отсутствует", icon=QMessageBox.Icon.Warning)
            return

        query = "DELETE FROM spaces.images WHERE id_image = %s"
        values = (self.id_image,)

        conn = None
        try:
            config = connection.load_config()
            conn = connection.db_connect(config)
            with conn:
                with conn.cursor() as cur:
                    cur.execute(query, values)
                    self.show_message("Успешно", f"Изображение с ID {self.id_image} удалено")
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            self.show_message("Ошибка при удалении", str(e), icon=QMessageBox.Icon.Critical)
        finally:
            if conn:
                conn.close()