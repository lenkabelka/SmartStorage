from PyQt6.QtWidgets import (QWidget, QLabel, QTextEdit, QPushButton, QVBoxLayout, QLineEdit,
                             QMessageBox, QDialog, QFileDialog, QHBoxLayout, QApplication)
from PyQt6.QtGui import QIcon


class AddSpace(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить пространство")
        self.setWindowIcon(QIcon("icons/mini_logo.png"))

        # Создание виджетов
        self.name_edit = QLineEdit()
        self.description_edit = QTextEdit()

        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Отмена")

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Имя пространства*:"))
        layout.addWidget(self.name_edit)
        layout.addWidget(QLabel("Описание:"))
        layout.addWidget(self.description_edit)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Сигналы
        self.ok_button.clicked.connect(self.create_space)
        self.cancel_button.clicked.connect(self.reject)

    def create_space(self):
        if not self.name_edit.text():
            QMessageBox.warning(self, "Заполните обязательные поля",
                                "Пожалуйста укажите название пространства!")
        else:
            self.accept()

    def get_data(self):
        # Возвращаем имя и описание
        return {
            "name": self.name_edit.text(),
            "description": self.description_edit.toPlainText() if self.description_edit.toPlainText() else None,
        }