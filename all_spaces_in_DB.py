import connect_DB as connection

from PyQt6.QtWidgets import QDialog, QListWidget, QListWidgetItem, QVBoxLayout
from PyQt6.QtCore import pyqtSignal

def load_all_spaces_from_DB():
    config = connection.load_config()
    conn = connection.db_connect(config)

    try:
        with conn:
            with conn.cursor() as cursor:
                query = """
                    SELECT id_space, space_name, space_description
                    FROM spaces.spaces
                """
                cursor.execute(query)
                results = cursor.fetchall()
                if not results:
                    return None
                    #raise LookupError("В базе данных нет ни одного пространства")
                return results
    except Exception as e:
        raise RuntimeError(f"Ошибка загрузки пространств: {e}")
    finally:
        conn.close()


class SpacesList(QDialog):
    spaceDoubleClicked = pyqtSignal(int)

    def __init__(self, spaces=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Выберите пространство")
        self.spaces = spaces or []

        self.list_widget = QListWidget()
        self.list_widget.setUniformItemSizes(True)

        for space in self.spaces:
            text = f"{space[1]}\n{space[2]}"
            item = QListWidgetItem(text)
            item.setSizeHint(item.sizeHint())
            self.list_widget.addItem(item)

        self.list_widget.itemDoubleClicked.connect(self.on_double_click)

        layout = QVBoxLayout()
        layout.addWidget(self.list_widget)
        self.setLayout(layout)

        self.setModal(True)  # Сделать диалог модальным (блокирует остальные окна)

    def on_double_click(self, item):
        row = self.list_widget.row(item)
        self.spaceDoubleClicked.emit(row)
        print(f"Двойной клик по строке {row}")
        self.accept()  # Закрыть диалог с успешным завершением