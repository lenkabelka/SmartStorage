from PyQt6.QtWidgets import QMessageBox
from dataclasses import dataclass
from PyQt6.QtGui import QPixmap
import psycopg2
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


    def insert(self, cursor):
        query = """
            INSERT INTO spaces.images (id_parent_space, image, image_name)
            VALUES (%s, %s, %s)
            RETURNING id_image;
        """
        image_bytes = psycopg2.Binary(utils.pixmap_to_bytes(self.image))
        values = (self.id_parent_space, image_bytes, self.name)
        cursor.execute(query, values)
        self.id_image = cursor.fetchone()[0]
        self.reset_state()
        print(f"Изображение добавлено с ID: {self.id_image}")


    def update(self, cursor):
        if self.id_image is None:
            raise ValueError("Невозможно обновить: id_image отсутствует")

        query = """
            UPDATE spaces.images
            SET image_name = %s, image = %s
            WHERE id_image = %s;
        """
        image_bytes = psycopg2.Binary(utils.pixmap_to_bytes(self.image))
        values = (self.name, image_bytes, self.id_image)
        cursor.execute(query, values)
        self.reset_state()
        print(f"Изображение с ID {self.id_image} обновлено")


    def delete(self, cursor):
        if self.id_image is None:
            raise ValueError("Невозможно удалить: id_image отсутствует")

        query = "DELETE FROM spaces.images WHERE id_image = %s"
        values = (self.id_image,)
        cursor.execute(query, values)
        print(f"Изображение с ID {self.id_image} удалено")


def load_space_images(id_space: int, cursor) -> list[SpaceImage]:
    query = """
        SELECT id_image, id_parent_space, image, image_name
        FROM spaces.images
        WHERE id_parent_space = %s
    """
    cursor.execute(query, (id_space,))
    rows = cursor.fetchall()

    images = []
    for id_image_DB, id_parent_space_DB, image_bytes_DB, image_name_DB in rows:
        pixmap = QPixmap()
        if image_bytes_DB is not None:
            if image_bytes_DB is not None:
                print("image_bytes длина:", len(image_bytes_DB))
                try:
                    success = pixmap.loadFromData(image_bytes_DB)
                    print("QPixmap загрузка:", "успешно" if success else "не удалось")
                except Exception as e:
                    print(f"Исключение при загрузке изображения: {e}")
            else:
                print("image_bytes = None")
            pixmap.loadFromData(image_bytes_DB)

        try:
            image_from_DB = SpaceImage(
                id_image=id_image_DB,
                id_parent_space=id_parent_space_DB,
                image=pixmap,
                name=image_name_DB
            )
        except Exception as e:
            print(f"Ошибка при создании SpaceImage: {e}")
            raise

        images.append(image_from_DB)

    return images