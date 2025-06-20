from dataclasses import dataclass, field
from typing import Optional

from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtWidgets import QMessageBox, QGraphicsPixmapItem
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
    original_pixmap: QPixmap # pixmap для создания элементов на QGraphicsScene
    projection_width: Optional[float] = None  # DB
    projection_height: Optional[float] = None  # DB

    # Связь с родителем
    reference_to_parent_space: Optional["space.Space"] = None
    reference_to_parent_thing: Optional["thing.Thing"] = None  # !!!!!!!!!

    scaled_projection_pixmap: Optional[DraggablePixmapItem | QGraphicsPixmapItem] = None
    reference_to_parent_projection: Optional["Projection"] = None
    projection_description: Optional[str] = None  # DB
    x_pos: Optional[float] = None  # DB
    y_pos: Optional[float] = None  # DB
    z_pos: Optional[float] = None  # DB

    id_projection: Optional[int] = None  # DB
    id_parent_projection: Optional[int] = None  # DB
    id_parent_space: Optional[int] = None  # DB
    id_parent_thing: Optional[int] = None  # DB  !!!!!!

    sub_projections: list["Projection"] = field(default_factory=list)


    def __post_init__(self):
        self._db_fields = {
            'projection_name',
            'projection_image',
            'projection_width',
            'projection_height',
            'projection_description',
            'x_pos',
            'y_pos',
            'z_pos',
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

    def insert(self, cursor):
        query = """
            INSERT INTO spaces.projections (
                id_parent_projection, 
                id_parent_space,
                id_parent_thing,
                projection_name, 
                projection_description, 
                x_pos_in_parent_projection, 
                y_pos_in_parent_projection,
                z_pos,
                projection_image, 
                projection_width, 
                projection_height
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            self.z_pos,
            psycopg2.Binary(image_bytes),
            self.projection_width,
            self.projection_height
        )
        cursor.execute(query, values)
        self.id_projection = cursor.fetchone()[0]
        self.reset_state()
        print(f"Проекция добавлена с ID: {self.id_projection}")

    def update(self, cursor):
        if self.id_projection is None:
            raise ValueError("Невозможно обновить: id_projection отсутствует")

        query = """
            UPDATE spaces.projections
            SET 
                projection_name = %s,
                projection_description = %s,
                x_pos_in_parent_projection = %s,
                y_pos_in_parent_projection = %s,
                z_pos = %s,
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
            self.z_pos,
            psycopg2.Binary(image_bytes),
            self.projection_width,
            self.projection_height,
            self.id_projection
        )
        cursor.execute(query, values)
        self.reset_state()
        print(f"Проекция с ID {self.id_projection} обновлена")

    def delete(self, cursor):
        if self.id_projection is None:
            raise ValueError("Невозможно удалить: id_projection отсутствует")

        query = "DELETE FROM spaces.projections WHERE id_projection = %s"
        values = (self.id_projection,)
        cursor.execute(query, values)
        print(f"Проекция с ID {self.id_projection} удалена")


    def save_projection(self, cursor, subspaces=None, things=None):
        self.save(cursor)

        subprojections_to_remove = []

        if self.sub_projections:
            for sub_projection in self.sub_projections:
                if sub_projection.state == ObjectState.DELETED:
                    subprojections_to_remove.append(sub_projection)
                else:
                    # привязка к пространству
                    if subspaces and not sub_projection.id_parent_space:
                        parent_subspace = next(
                            (subspace for subspace in subspaces if
                             sub_projection.reference_to_parent_space == subspace),
                            None
                        )
                        if parent_subspace:
                            sub_projection.id_parent_space = parent_subspace.id_space

                    # привязка к вещи
                    if things and not sub_projection.id_parent_thing:
                        parent_thing = next(
                            (th for th in things if sub_projection.reference_to_parent_thing == th),
                            None
                        )
                        if parent_thing:
                            sub_projection.id_parent_thing = parent_thing.id_thing

                    # привязка к родительской проекции
                    if not sub_projection.id_parent_projection:
                        sub_projection.id_parent_projection = self.id_projection

                    sub_projection.save(cursor)

            for sub_projection in subprojections_to_remove:
                self.sub_projections.remove(sub_projection)