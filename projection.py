from dataclasses import dataclass, field
from typing import Optional

from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtWidgets import QMessageBox, QGraphicsPixmapItem
import psycopg2

from draggable_pixmap_item import DraggablePixmapItem
import space
import track_object_state
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


    def copy(self, with_subprojections: bool = True) -> "Projection":
        """
        - IDs не сбрасываем
        - QImage/QPixmap передаём по ссылке
        - scaled_projection_pixmap создаём заново (именно это отображается на мини сцене)
        """

        # --- scaled pixmap item ---
        new_pixmap_item = QGraphicsPixmapItem(self.original_pixmap)

        # --- создаём копию самой развёртки ---
        new_proj = Projection(
            projection_name=self.projection_name,
            projection_image=self.projection_image,  # ссылка
            original_pixmap=self.original_pixmap,  # ссылка
            projection_width=self.projection_width,
            projection_height=self.projection_height,
            projection_description=self.projection_description,
            x_pos=self.x_pos,
            y_pos=self.y_pos,
            z_pos=self.z_pos,

            # ID НЕ СБРАСЫВАЕМ
            id_projection=self.id_projection,
            id_parent_projection=self.id_parent_projection,
            id_parent_space=self.id_parent_space,
            id_parent_thing=self.id_parent_thing,

            scaled_projection_pixmap=new_pixmap_item,  # новый item

            reference_to_parent_space=self.reference_to_parent_space,
            reference_to_parent_thing=self.reference_to_parent_thing,
            reference_to_parent_projection=self.reference_to_parent_projection,
        )

        new_proj._state = self._state  # копируем state
        new_proj._original_values = dict(self._original_values)  # копируем оригинальные значения
        new_proj._db_fields = set(self._db_fields)  # копируем поля БД
        new_proj._non_db_fields = set(self._non_db_fields)  # если есть

        # 4. Рекурсивно копируем sub_projections
        if with_subprojections:
            new_proj.sub_projections = []
            for sub in self.sub_projections:
                sub_copy = sub.copy(with_subprojections=False)

                # Устанавливаем правильного родителя
                sub_copy.reference_to_parent_projection = new_proj

                # Корректируем tracking-состояние и значения
                sub_copy._state = sub._state
                sub_copy._original_values = dict(sub._original_values)
                sub_copy._db_fields = set(sub._db_fields)
                sub_copy._non_db_fields = set(sub_copy._non_db_fields)  # если есть

                new_proj.sub_projections.append(sub_copy)

        return new_proj


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

        if cursor.rowcount == 0:
            raise ValueError(f"Проекция с ID {self.id_projection} не найдена в базе")

        self.reset_state()
        print(f"Проекция с ID {self.id_projection} обновлена")


    def delete(self, cursor):
        if self.id_projection is None:
            raise ValueError("Невозможно удалить: id_projection отсутствует")

        query = "DELETE FROM spaces.projections WHERE id_projection = %s"
        values = (self.id_projection,)
        cursor.execute(query, values)

        if cursor.rowcount == 0:
            raise ValueError(f"Проекция с ID {self.id_projection} не найдена в базе")

        print(f"Проекция с ID {self.id_projection} удалена")


    def save_projection(self, cursor, subspaces=None, things=None):
        self.save(cursor)

        subprojections_to_remove = []

        if self.sub_projections:
            for sub_projection in self.sub_projections:
                if sub_projection.state == ObjectState.DELETED:
                    subprojections_to_remove.append(sub_projection)
                    sub_projection.save(cursor)
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


def load_space_projections(space_in_DB, cursor, space, subspaces=None, things=None) -> list[Projection]:

    # Загружаем только развертки. Подразвертки не загружаем в список разверток id_parent_projection IS NULL
    query = """
        SELECT 
            id_projection, 
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
        FROM spaces.projections
        WHERE id_parent_space = %s
            AND id_parent_projection IS NULL;
    """
    cursor.execute(query, (space_in_DB.id_space,))
    rows = cursor.fetchall()

    projections = []

    for row in rows:
        (
            id_projection_DB,
            id_parent_projection_DB,
            id_parent_space_DB,
            id_parent_thing_DB,
            projection_name_DB,
            projection_description_DB,
            x_pos_DB,
            y_pos_DB,
            z_pos_DB,
            image_bytes,
            width_DB,
            height_DB
        ) = row
        # из БД приходит Decimal вместо float
        width_DB = float(width_DB) if width_DB is not None else None
        height_DB = float(height_DB) if height_DB is not None else None
        x_pos_DB = float(x_pos_DB) if x_pos_DB is not None else None
        y_pos_DB = float(y_pos_DB) if y_pos_DB is not None else None
        z_pos_DB = float(z_pos_DB) if z_pos_DB is not None else None

        # Преобразуем байты в QImage
        image = QImage()
        if image_bytes:
            image = image.fromData(image_bytes)
            print(type(image))
            if not image:
                print("Не удалось загрузить QImage из байтов")
        else:
            continue  # пропускаем пустую проекцию

        # Получаем масштабированный и обрезанный pixmap
        scaled_cropped_pixmap = utils.get_scaled_cropped_pixmap(image, width_DB, height_DB)

        try:
            projection_from_DB = Projection(
                projection_name=projection_name_DB,
                projection_image=image,
                projection_width=width_DB,
                projection_height=height_DB,
                projection_description=projection_description_DB,
                x_pos=x_pos_DB,
                y_pos=y_pos_DB,
                z_pos=z_pos_DB,
                id_projection=id_projection_DB,
                id_parent_projection=id_parent_projection_DB,
                id_parent_space=id_parent_space_DB,
                id_parent_thing=id_parent_thing_DB,
                original_pixmap=scaled_cropped_pixmap,
                scaled_projection_pixmap=QGraphicsPixmapItem(scaled_cropped_pixmap),

                reference_to_parent_space=space
            )

            projection_from_DB.sub_projections = load_projection_subprojections(projection_from_DB, cursor, subspaces=subspaces, things=things)

            print(f"projection_from_DB.sub_projections: {projection_from_DB.sub_projections}")

        except Exception as e:
            print(f"Ошибка при создании Projection: {e}")
            continue

        projections.append(projection_from_DB)

    return projections


def load_projection_subprojections(proj: Projection, cursor, subspaces=None, things=None) -> list[Projection]:

    query = """
        SELECT 
            id_projection, 
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
        FROM spaces.projections
        WHERE id_parent_projection = %s
        ORDER BY z_pos
    """
    cursor.execute(query, (proj.id_projection,))
    rows = cursor.fetchall()

    subprojections = []

    for row in rows:
        (
            id_projection_DB,
            id_parent_projection_DB,
            id_parent_space_DB,
            id_parent_thing_DB,
            projection_name_DB,
            projection_description_DB,
            x_pos_DB,
            y_pos_DB,
            z_pos_DB,
            image_bytes,
            width_DB,
            height_DB
        ) = row
        # из БД приходит Decimal вместо float
        width_DB = float(width_DB) if width_DB is not None else None
        height_DB = float(height_DB) if height_DB is not None else None
        x_pos_DB = float(x_pos_DB) if x_pos_DB is not None else None
        y_pos_DB = float(y_pos_DB) if y_pos_DB is not None else None
        z_pos_DB = float(z_pos_DB) if z_pos_DB is not None else None

        # Преобразуем байты в QImage
        #image = QImage()
        if image_bytes:
            image = QImage.fromData(image_bytes)
            print(type(image))
            if image.isNull():
                print("Не удалось загрузить QImage из байтов")
        else:
            print("Нет изображения в базе")
            continue  # пропускаем пустую проекцию

        x_scale = proj.original_pixmap.width() / proj.projection_width
        y_scale = proj.original_pixmap.height() / proj.projection_height

        original_pixmap = utils.get_scaled_pixmap(
            image,
            int(round(x_scale * width_DB)),
            int(round(y_scale * height_DB))
        )


        try:
            subprojection = Projection(
                projection_name=projection_name_DB,
                projection_image=image,
                projection_width=width_DB,
                projection_height=height_DB,
                projection_description=projection_description_DB,
                x_pos=x_pos_DB,
                y_pos=y_pos_DB,
                z_pos=z_pos_DB,
                id_projection=id_projection_DB,
                id_parent_projection=id_parent_projection_DB,
                id_parent_space=id_parent_space_DB,
                id_parent_thing=id_parent_thing_DB,
                original_pixmap=original_pixmap
            )

            subprojection.reference_to_parent_projection = proj

            # привязка к подпространству
            if subspaces is not None and id_parent_space_DB is not None:
                parent_subspace = next(
                    (subspace for subspace in subspaces if
                     subprojection.id_parent_space == id_parent_space_DB),
                    None
                )
                if parent_subspace:
                    subprojection.reference_to_parent_space = parent_subspace

            # привязка к вещи
            if things is not None and id_parent_thing_DB is not None:
                parent_thing = next(
                    (th for th in things if subprojection.id_parent_thing == id_parent_thing_DB),
                    None
                )
                if parent_thing:
                    subprojection.reference_to_parent_thing = parent_thing


        except Exception as e:
            print(f"Ошибка при создании Projection: {e}")
            continue

        subprojections.append(subprojection)

    return subprojections