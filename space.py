import random
from dataclasses import dataclass, field
from typing import Optional
from PyQt6.QtWidgets import QMessageBox
import projection
import track_object_state
import image as im
import connect_DB as connection
import psycopg2
import thing as th
from track_object_state import ObjectState


@dataclass
class Space(track_object_state.Trackable):
    name: str  # DB
    description: str = None  # DB
    projections: list[Optional["projection.Projection"]] = field(default_factory=list)
    current_projection: Optional["projection.Projection"] = None
    subspaces: list["Space"] = field(default_factory=list)
    space_images: list[Optional[im.SpaceImage]] = field(default_factory=list)
    id_space: Optional[int] = None  # DB
    id_parent_space: Optional[int] = None  # DB
    things: list[Optional["th.Thing"]] = field(default_factory=list)


    def __post_init__(self):
        self._db_fields = {'id_space', 'name', 'description', 'id_parent_space'}
        super().__post_init__()


    def show_message(self, title: str, message: str, icon=QMessageBox.Icon.Critical):
        msg = QMessageBox()
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setIcon(icon)
        msg.exec()


    def insert(self, cursor):
        try:
            query = """
                INSERT INTO spaces.spaces (id_parent_space, space_name, space_description)
                VALUES (%s, %s, %s)
                RETURNING id_space;
            """
            values = (self.id_parent_space, self.name, self.description)
            cursor.execute(query, values)
            self.id_space = cursor.fetchone()[0]
            self.reset_state()
            print(f"{self.name} space inserted")
        except Exception as e:
            raise ValueError(f"Ошибка при вставке пространства '{self.name}': {e}")


    def update(self, cursor):
        """
        Обновляет запись о пространстве в таблице spaces.spaces.
        """
        if self.id_space is None:
            raise ValueError("Невозможно обновить: id_space отсутствует")

        query = """
            UPDATE spaces.spaces
            SET space_name = %s,
                space_description = %s,
                id_parent_space = %s
            WHERE id_space = %s
        """
        values = (self.name, self.description, self.id_parent_space, self.id_space)

        cursor.execute(query, values)

        if cursor.rowcount == 0:
            raise ValueError(f"Пространство с id_space={self.id_space} не найдено в базе")

        self.reset_state()
        print(f"Space '{self.name}' updated (id_space={self.id_space})")


    def delete(self, cursor):
        if self.id_space is None:
            raise ValueError("Невозможно удалить: id_space отсутствует")

        query = "DELETE FROM spaces.spaces WHERE id_space = %s"
        values = (self.id_space,)
        cursor.execute(query, values)

        if cursor.rowcount == 0:
            raise ValueError(f"Пространство с id_space={self.id_space} не найдено в базе")

        print(f"{self.name} space deleted")


    def save_space(self, schow_message=True):
        config = connection.load_config()
        conn = connection.db_connect(config)

        try:
            with conn:
                with conn.cursor() as cursor:

                    subspaces_to_delete = []
                    things_to_delete = []
                    projections_to_delete = []
                    images_to_delete = []

                    # save current space
                    self.save(cursor=cursor)

                    # subspaces
                    if self.subspaces:
                        for subspace in self.subspaces:
                            if not subspace.id_parent_space:
                                subspace.id_parent_space = self.id_space
                            if subspace.state == ObjectState.DELETED:
                                subspaces_to_delete.append(subspace)
                            subspace.save(cursor=cursor)

                    # things
                    if self.things:
                        for thg in self.things:
                            if not thg.id_parent_space:
                                thg.id_parent_space = self.id_space
                            if thg.state == ObjectState.DELETED:
                                things_to_delete.append(thg)
                            thg.save_thing(cursor=cursor)

                    # projections
                    if self.projections:
                        for project in self.projections:
                            if not project.id_parent_space:
                                project.id_parent_space = self.id_space
                            if project.state == ObjectState.DELETED:
                                projections_to_delete.append(project)
                            if self.subspaces or self.things:
                                project.save_projection(cursor=cursor, subspaces=self.subspaces, things=self.things)
                            else:
                                project.save_projection(cursor=cursor)

                    # images
                    if self.space_images:
                        for image in self.space_images:
                            if not image.id_parent_space:
                                image.id_parent_space = self.id_space
                            if image.state == ObjectState.DELETED:
                                images_to_delete.append(image)
                            image.save(cursor=cursor)

                    # remove deleted
                    for lst, deleted in [
                        (self.space_images, images_to_delete),
                        (self.projections, projections_to_delete),
                        (self.subspaces, subspaces_to_delete),
                        (self.things, things_to_delete)
                    ]:
                        for obj in deleted:
                            lst.remove(obj)

                # Сообщение смотрим только по состоянию самого пространства
                if getattr(self, "state", None) == ObjectState.DELETED:
                    self.show_message("Внимание", "Пространство удалено.")
                else:
                    if schow_message:
                        self.show_message("Успешно", "Пространство сохранено.")

        except Exception as e:
            self.show_message("Ошибка", f"Сохранение не удалось: {str(e)}",
                              icon=QMessageBox.Icon.Critical)


def load_space_by_id(id_space: int) -> Space:
    config = connection.load_config()
    conn = connection.db_connect(config)

    try:
        with conn:
            with conn.cursor() as cursor:
                query = """
                    SELECT id_space, id_parent_space, space_name, space_description
                    FROM spaces.spaces
                    WHERE id_space = %s
                """
                cursor.execute(query, (id_space,))
                row = cursor.fetchone()
                if row is None:
                    raise LookupError(f"Пространство с id={id_space} не найдено")

                id_space_db, id_parent_space, name, description = row
                space_from_DB = Space(
                    id_space=id_space_db,
                    id_parent_space=id_parent_space,
                    name=name,
                    description=description
                )

                space_from_DB.space_images = im.load_images_for_parent(id_space_db, "space", cursor)
                space_from_DB.subspaces = load_space_subspaces(id_space_db, cursor)
                space_from_DB.things = th.load_space_things(space_from_DB, cursor)
                space_from_DB.projections = projection.load_space_projections(space_from_DB, cursor)

                return space_from_DB
    finally:
        conn.close()


def load_space_subspaces(id_space: int, cursor) -> list[Space]:
    query = """
        SELECT id_space, id_parent_space, space_name, space_description
        FROM spaces.spaces
        WHERE id_parent_space = %s
    """
    cursor.execute(query, (id_space,))
    rows = cursor.fetchall()

    subspaces = []

    for id_space_DB, id_parent_space_DB, space_name_DB, space_description_DB in rows:
        try:
            subspace = Space(
                id_space=id_space_DB,
                id_parent_space=id_parent_space_DB,
                name=space_name_DB,
                description=space_description_DB
            )
            # Рекурсивно загружаем подпространства для этого подпространства
            subspace.subspaces = load_space_subspaces(subspace.id_space, cursor)

            # Загружаем вещи для этого подпространства
            subspace.things = th.load_space_things(subspace, cursor)


        except Exception as e:
            print(f"Ошибка при создании подпространства Space: {e}")
            raise

        subspaces.append(subspace)

    return subspaces


def get_top_space_id(starting_parent_id):
    """
    Итеративно находит самый верхний ancestor space, у которого id_parent_space IS NULL.
    """
    config = connection.load_config()
    conn = connection.db_connect(config)

    try:
        with conn:
            with conn.cursor() as cursor:
                current_id = starting_parent_id

                while current_id is not None:
                    cursor.execute(
                        "SELECT id_space, id_parent_space FROM spaces.spaces WHERE id_space = %s",
                        (current_id,)
                    )
                    result = cursor.fetchone()

                    if result is None:
                        raise ValueError(f"Пространство с id={current_id} не найдено в базе данных")

                    id_space, parent_id = result

                    if parent_id is None:
                        return id_space  # нашли корень
                    else:
                        current_id = parent_id
    except Exception as e:
        print(f"Ошибка при поиске верхнего пространства: {e}")
        raise