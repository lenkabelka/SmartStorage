from dataclasses import dataclass, field
from typing import Optional

from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtWidgets import QMessageBox
import psycopg2

from draggable_pixmap_item import DraggablePixmapItem
import space
import track_object_state
import connect_DB as connection
import utils as utils
from track_object_state import ObjectState
import thing


@dataclass
class Projection(track_object_state.Trackable):
    projection_name: str  # DB
    projection_image: QImage  # DB
    projection_width: Optional[float] = None  # DB
    projection_height: Optional[float] = None  # DB

    # Связь с родителем
    reference_to_parent_space: Optional["space.Space"] = None
    reference_to_parent_thing: Optional["thing.Thing"] = None  # !!!!!!!!!

    scaled_projection_pixmap: Optional[DraggablePixmapItem | QPixmap] = None
    reference_to_parent_projection: Optional["Projection"] = None
    projection_description: Optional[str] = None  # DB
    x_pos: Optional[float] = None  # DB
    y_pos: Optional[float] = None  # DB

    id_projection: Optional[int] = None  # DB
    id_parent_projection: Optional[int] = None  # DB
    id_parent_space: Optional[int] = None  # DB
    id_parent_thing: Optional[int] = None  # DB  !!!!!!

    sub_projections: list["Projection"] = field(default_factory=list)

    # def get_parent(self):
    #     return self.reference_to_parent_space or self.reference_to_parent_thing

    # def validate_parent(self):
    #     if (self.reference_to_parent_space is not None) and (self.reference_to_parent_thing is not None):
    #         raise ValueError("Projection cannot have both space and thing as parent.")

    def __post_init__(self):
        self._db_fields = {
            'projection_name',
            'projection_image',
            'projection_width',
            'projection_height',
            'projection_description',
            'x_pos',
            'y_pos',
            'id_projection',
            'id_parent_projection',
            'id_parent_space',
            'id_parent_thing'
        }
        super().__post_init__()

    # id_projection
    # id_parent_projection
    # id_parent_space
    # projection_name
    # projection_description
    # x_pos_in_parent_projection
    # y_pos_in_parent_projection
    # projection_image
    # projection_width
    # projection_height
    def show_message(self, title: str, message: str, icon=QMessageBox.Icon.Information):
        msg = QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setIcon(icon)
        msg.exec()

    def insert(self):
        query = """
            INSERT INTO spaces.projections (
                id_parent_projection, 
                id_parent_space,
                id_parent_thing,
                projection_name, 
                projection_description, 
                x_pos_in_parent_projection, 
                y_pos_in_parent_projection, 
                projection_image, 
                projection_width, 
                projection_height
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_projection;
        """
        image_bytes = utils.pixmap_to_bytes(QPixmap(self.projection_image))
        values = (
            self.id_parent_projection,
            self.id_parent_space,
            self.id_parent_thing,
            self.projection_name,
            self.projection_description,
            self.x_pos,
            self.y_pos,
            psycopg2.Binary(image_bytes),
            self.projection_width,
            self.projection_height
        )

        conn = None
        try:
            config = connection.load_config()
            conn = connection.db_connect(config)
            with conn:
                with conn.cursor() as cur:
                    cur.execute(query, values)
                    self.id_projection = cur.fetchone()[0]
                    self.show_message("Успешно", f"Проекция добавлена с ID: {self.id_projection}")
                    self.reset_state()
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            self.show_message("Ошибка при вставке", str(e), icon=QMessageBox.Icon.Critical)
        finally:
            if conn:
                conn.close()

    def update(self):
        if self.id_projection is None:
            self.show_message("Ошибка", "Невозможно обновить: id_projection отсутствует", icon=QMessageBox.Icon.Warning)
            return

        query = """
            UPDATE spaces.projections
            SET 
                projection_name = %s,
                projection_description = %s,
                x_pos_in_parent_projection = %s,
                y_pos_in_parent_projection = %s,
                projection_image = %s,
                projection_width = %s,
                projection_height = %s
            WHERE id_projection = %s
        """

        image_bytes = utils.pixmap_to_bytes(QPixmap(self.projection_image))
        values = (
            self.projection_name,
            self.projection_description,
            self.x_pos,
            self.y_pos,
            psycopg2.Binary(image_bytes),
            self.projection_width,
            self.projection_height,
            self.id_projection
        )

        conn = None
        try:
            config = connection.load_config()
            conn = connection.db_connect(config)
            with conn:
                with conn.cursor() as cur:
                    cur.execute(query, values)
                    self.show_message("Успешно", f"Проекция с ID {self.id_projection} обновлена")
                    self.reset_state()
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            self.show_message("Ошибка при обновлении", str(e), icon=QMessageBox.Icon.Critical)
        finally:
            if conn:
                conn.close()

    def delete(self):
        if self.id_projection is None:
            self.show_message("Ошибка", "Невозможно удалить: id_projection отсутствует", icon=QMessageBox.Icon.Warning)
            return

        query = "DELETE FROM spaces.projections WHERE id_projection = %s"
        values = (self.id_projection,)

        conn = None
        try:
            config = connection.load_config()
            conn = connection.db_connect(config)
            with conn:
                with conn.cursor() as cur:
                    cur.execute(query, values)
                    self.show_message("Успешно", f"Проекция с ID {self.id_projection} удалена")
        except psycopg2.Error as e:
            if conn:
                conn.rollback()
            self.show_message("Ошибка при удалении", str(e), icon=QMessageBox.Icon.Critical)
        finally:
            if conn:
                conn.close()


    def save_projection(self, subspaces=None):
        self.save()

        subprojections_to_remove = []

        if self.sub_projections:
            for sub_projection in self.sub_projections:
                if subspaces:

                    if sub_projection.state == ObjectState.DELETED:
                        subprojections_to_remove.append(sub_projection)
                        sub_projection.save()

                    else:
                        if not sub_projection.id_parent_space:
                            parent_subspace = next((subspace for subspace in subspaces if sub_projection.reference_to_parent_space == subspace), None)
                            if parent_subspace:
                                sub_projection.id_parent_space = parent_subspace.id_space

                        if not sub_projection.id_parent_projection:
                            sub_projection.id_parent_projection = self.id_projection

                        sub_projection.save()


        if subprojections_to_remove:
            for sub_projection in self.sub_projections:
                self.sub_projections.remove(sub_projection)