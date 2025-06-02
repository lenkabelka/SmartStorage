from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QHBoxLayout, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt
import space
import connect_DB
import sys


class SpaceListDialog(QDialog):
    def __init__(self, spaces: list[space.Space], on_select_callback=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Список пространств")
        self.resize(600, 400)

        self.spaces = spaces
        self.on_select_callback = on_select_callback

        self.layout = QVBoxLayout(self)

        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Имя пространства", "Описание"])
        self.table.setRowCount(len(self.spaces))
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setWordWrap(True)
        self.table.setHorizontalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)
        self.table.setVerticalScrollMode(QTableWidget.ScrollMode.ScrollPerPixel)

        # Заполнение таблицы
        for row, space in enumerate(self.spaces):
            name_item = QTableWidgetItem(space.name)
            desc_item = QTableWidgetItem(space.description or "")

            name_item.setFlags(name_item.flags() ^ Qt.ItemFlag.ItemIsEditable)
            desc_item.setFlags(desc_item.flags() ^ Qt.ItemFlag.ItemIsEditable)

            self.table.setItem(row, 0, name_item)
            self.table.setItem(row, 1, desc_item)

        self.table.doubleClicked.connect(self.handle_double_click)

        self.table.resizeColumnsToContents()
        self.table.resizeRowsToContents()
        self.table.horizontalHeader().setStretchLastSection(True)

        self.layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        self.layout.addLayout(btn_layout)

    def handle_double_click(self, index):
        row = index.row()
        selected_space = self.spaces[row]
        if self.on_select_callback:
            self.on_select_callback(selected_space)
        self.accept()


def open_space_details(space: space.Space):
    QMessageBox.information(
        None,
        "Вы выбрали пространство",
        f"Имя: {space.name}\nОписание: {space.description or ''}"
    )


# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#
#     try:
#         space_list = load_all_spaces()
#     except Exception as e:
#         QMessageBox.critical(None, "Ошибка загрузки", f"Не удалось загрузить пространства:\n{e}")
#         sys.exit(1)
#
#     dialog = SpaceListDialog(space_list, on_select_callback=open_space_details)
#     dialog.exec()
#
#     sys.exit(0)
