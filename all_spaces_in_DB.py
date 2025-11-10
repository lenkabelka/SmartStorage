import connect_DB as connection

from PyQt6.QtWidgets import QDialog, QListWidget, QListWidgetItem, QVBoxLayout, QWidget, QLabel, QSizePolicy
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import pyqtSignal, Qt
import utils

def load_all_spaces_from_DB(user_id, global_role):
    config = connection.load_config()
    conn = connection.db_connect(config)

    try:
        with conn:
            with conn.cursor() as cursor:
                if global_role == "admin":
                    # Админ видит абсолютно все пространства
                    query = """
                            SELECT id_space, space_name, space_description
                            FROM spaces.spaces
                            ORDER BY space_name ASC
                        """
                    cursor.execute(query)
                else:
                    # Остальные видят только свои пространства, где им назначена локальная роль
                    query = """
                            SELECT s.id_space, s.space_name, s.space_description
                            FROM spaces.spaces s
                            JOIN spaces.user_access ua ON s.id_space = ua.id_space
                            WHERE ua.id_user = %s
                            ORDER BY s.space_name ASC
                        """
                    cursor.execute(query, (user_id,))

                results = cursor.fetchall()
                return results or []
    except Exception as e:
        raise RuntimeError(f"Ошибка загрузки пространств: {e}")
    finally:
        conn.close()


def load_all_non_subspaces_from_DB(user_id, global_role, root_space_id):
    """
    Загружает все пространства, доступные пользователю, исключая указанное пространство
    и все его подпространства (рекурсивно).
    """
    if root_space_id is None:
        raise ValueError("root_space_id не может быть None")

    config = connection.load_config()
    conn = connection.db_connect(config)

    try:
        with conn:
            with conn.cursor() as cursor:

                recursive_cte = """
                    WITH RECURSIVE subspaces AS (
                        SELECT id_space
                        FROM spaces.spaces
                        WHERE id_space = %s
                        UNION ALL
                        SELECT s.id_space
                        FROM spaces.spaces s
                        INNER JOIN subspaces ss ON s.id_parent_space = ss.id_space
                    )
                """

                if global_role == "admin":
                    query = f"""
                        {recursive_cte}
                        SELECT s.id_space, s.space_name, s.space_description
                        FROM spaces.spaces s
                        WHERE s.id_space != %s
                          AND s.id_space NOT IN (SELECT id_space::INTEGER FROM subspaces)
                        ORDER BY s.space_name ASC;
                    """
                    cursor.execute(query, (root_space_id, root_space_id))

                else:
                    query = f"""
                        {recursive_cte}
                        SELECT s.id_space, s.space_name, s.space_description
                        FROM spaces.spaces s
                        JOIN spaces.user_access ua ON s.id_space = ua.id_space
                        WHERE ua.id_user = %s
                          AND s.id_space != %s
                          AND s.id_space NOT IN (SELECT id_space::INTEGER FROM subspaces)
                        ORDER BY s.space_name ASC;
                    """
                    cursor.execute(query, (root_space_id, user_id, root_space_id))

                results = cursor.fetchall()
                return results or []

    except Exception as e:
        raise RuntimeError(f"Ошибка загрузки пространств (без подпространств): {e}")

    finally:
        conn.close()




class SpacesList(QDialog):
    spaceDoubleClicked = pyqtSignal(int)

    def __init__(self, show_space_description = True, spaces=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выберите пространство")
        self.setWindowIcon(QIcon(utils.resource_path("icons/mini_logo.png")))
        self.spaces = spaces or []

        # Основной QListWidget
        self.list_widget = QListWidget()
        self.list_widget.setUniformItemSizes(False)  # отключаем, чтобы элементы разной высоты работали

        # Заполнение списка кастомными элементами
        for space in self.spaces:
            if space[1] is not None:
                widget = QWidget()
                layout = QVBoxLayout(widget)
                layout.setContentsMargins(0, 0, 0, 0)
                self.list_widget.setSpacing(0)

                # HTML для имени и описания с разными шрифтами
                html = f"""
                <p style='margin:0; font-family: Arial; font-size:14pt; font-weight:bold;'>{space[1]}</p>
                """
                if space[2] and show_space_description:
                    html += f"""
                    <p style='margin:0; font-family:"Times New Roman"; font-size:11pt; font-style:italic; color:#35a0a2; margin-left:8px;'>{space[2]}</p>
                    """

                label = QLabel()
                label.setTextFormat(Qt.TextFormat.RichText)
                label.setWordWrap(True)  # перенос длинного текста
                label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
                label.setText(html)
                layout.addWidget(label)

                # Создаем QListWidgetItem и вставляем кастомный виджет
                item = QListWidgetItem()
                item.setSizeHint(widget.sizeHint())  # учитываем новую высоту
                self.list_widget.addItem(item)
                self.list_widget.setItemWidget(item, widget)

        # Обработка двойного клика и Enter
        self.list_widget.itemActivated.connect(self.on_item_activated)

        # Основной layout диалога
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.list_widget)
        self.setLayout(main_layout)

        self.setModal(True)

    def on_item_activated(self, item):
        """Обработка выбора элемента списка"""
        row = self.list_widget.row(item)
        self.spaceDoubleClicked.emit(row)
        print(f"Двойной клик по строке {row}")
        self.accept()