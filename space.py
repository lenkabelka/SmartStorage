from dataclasses import dataclass, field
from typing import Optional
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtGui import QPixmap
import projection
import track_object_state
import image as im
import queries_for_DB as q
import psycopg2


@dataclass
class Space(track_object_state.Trackable):
    name: str  # DB
    description: str = None  # DB
    projections: list[projection.Projection] = field(default_factory=list)
    current_projection: Optional[projection.Projection] = None
    subspaces: list["Space"] = field(default_factory=list)
    space_images: list[Optional[im.SpaceImage]] = field(default_factory=list)
    id_space: Optional[int] = None  # DB
    id_parent_space: Optional[int] = None  # DB

    def __post_init__(self):
        self._db_fields = {'id_space', 'name', 'description'}
        super().__post_init__()


    def show_message(self, title: str, message: str, icon=QMessageBox.Icon.Information):
        msg = QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setIcon(icon)
        msg.exec()


    # id_space
    # id_parent_space
    # space_name
    # space_description
    def insert(self):
        query = """
            INSERT INTO spaces.spaces (id_parent_space, space_name, space_description)
            VALUES (%s, %s, %s)
            RETURNING id_space;
        """
        values = (self.id_parent_space, self.name, self.description)
        conn = None
        try:
            config = q.load_config()
            conn = q.db_connect(config)
            with conn:
                with conn.cursor() as cur:
                    cur.execute(query, values)
                    self.id_space = cur.fetchone()[0]
                    self.show_message("Успешно", f"Объект добавлен с ID: {self.id_space}")
                    self.reset_state()  # обновляем состояние и оригинальные значения
                    print(f"{self.name} space inserted")
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            self.show_message("Ошибка при вставке", str(e), icon=QMessageBox.Icon.Critical)
        finally:
            if conn:
                conn.close()


    def update(self):
        if self.id_space is None:
            self.show_message("Ошибка", "Невозможно обновить: id_space отсутствует", icon=QMessageBox.Icon.Warning)
            return
        query = """
            UPDATE spaces.spaces
            SET space_name = %s, space_description = %s
            WHERE id_space = %s
        """
        values = (self.name, self.description, self.id_space)
        conn = None
        try:
            config = q.load_config()
            conn = q.db_connect(config)
            with conn:
                with conn.cursor() as cur:
                    cur.execute(query, values)
                    self.show_message("Успешно", f"Объект с ID {self.id_space} обновлён")
                    self.reset_state()  # обновляем состояние и оригинальные значения
                    print(f"{self.name} space updated")
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            self.show_message("Ошибка при обновлении", str(e), icon=QMessageBox.Icon.Critical)
        finally:
            if conn:
                conn.close()


    def delete(self):
        if self.id_space is None:
            self.show_message("Ошибка", "Невозможно удалить: id_space отсутствует", icon=QMessageBox.Icon.Warning)
            return
        query = "DELETE FROM spaces.spaces WHERE id_space = %s"
        values = (self.id_space,)
        conn = None
        try:
            config = q.load_config()
            conn = q.db_connect(config)
            with conn:
                with conn.cursor() as cur:
                    cur.execute(query, values)
                    self.show_message("Успешно", f"Объект с ID {self.id_space} удалён")
                    print(f"{self.name} space deleted")
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            self.show_message("Ошибка при удалении", str(e), icon=QMessageBox.Icon.Critical)
        finally:
            if conn:
                conn.close()