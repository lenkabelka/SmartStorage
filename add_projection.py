from PyQt6.QtWidgets import (QWidget, QLabel, QTextEdit, QPushButton, QVBoxLayout, QLineEdit,
                             QMessageBox, QDialog, QFileDialog, QHBoxLayout, QApplication)
from PyQt6.QtGui import QFontMetrics, QFont, QGuiApplication, QRegularExpressionValidator, QIcon, QPixmap
from PyQt6.QtCore import Qt, QRegularExpression, pyqtSignal, QBuffer, QByteArray
import sys


class AddSpaceOrSubspace(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить пространство")
        self.selected_file = ""

        # Создание виджетов
        self.name_edit = QLineEdit()
        self.description_edit = QTextEdit()

        # Добавлены два QLineEdit для ввода коэффициентов масштабирования
        self.x_scale_edit = QLineEdit()
        self.y_scale_edit = QLineEdit()

        # Установка начальных значений (например, 1 для коэффициента масштаба)
        self.x_scale_edit.setText("1")
        self.y_scale_edit.setText("1")

        self.image_label = QLabel("Нет изображения")

        screen_size = QGuiApplication.primaryScreen().size()
        screen_width = screen_size.width()
        screen_height = screen_size.height()
        width_coef = 0.3    #coefizient for width of Add Comment window
        height_coef = 0.2   #coefizient for height of Add Comment window
        self.image_label.setFixedSize(int(screen_width * width_coef), int(screen_height * height_coef))
        self.image_label.setStyleSheet("border: 1px solid gray;")

        self.load_button = QPushButton("Загрузить картинку")
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Отмена")

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Имя пространства:"))
        layout.addWidget(self.name_edit)
        layout.addWidget(QLabel("Описание:"))
        layout.addWidget(self.description_edit)

        layout.addWidget(QLabel("Картинка:"))
        layout.addWidget(self.image_label)

        # Добавление этих полей в layout
        layout_for_scales = QHBoxLayout()
        layout_for_scales.addWidget(QLabel("Коэффициент масштаба по X:"))
        layout_for_scales.addWidget(self.x_scale_edit)
        layout_for_scales.addWidget(QLabel("Коэффициент масштаба по Y:"))
        layout_for_scales.addWidget(self.y_scale_edit)

        layout.addLayout(layout_for_scales)

        layout.addWidget(self.load_button)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Переменная для хранения изображения
        self.pixmap = None

        # Сигналы
        self.load_button.clicked.connect(self.load_image)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выбрать изображение", "", "Images (*.png *.jpg *.bmp)"
        )
        if file_path:
            self.pixmap = QPixmap(file_path)
            if self.pixmap.isNull():
                QMessageBox.warning(self, "Ошибка", "Не удалось загрузить изображение.")
            else:
                # Масштабирование с сохранением пропорций
                scaled = self.pixmap.scaled(
                    self.image_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                # Центрируем изображение в QLabel
                self.image_label.setPixmap(scaled)
                self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)


    def get_data(self):
        # Возвращаем имя, описание, картинку в байтах и коэффициенты масштабирования
        return {
            "name": self.name_edit.text(),
            "description": self.description_edit.toPlainText(),
            "image": self.pixmap if self.pixmap else None,
            "x_scale": float(self.x_scale_edit.text()),
            "y_scale": float(self.y_scale_edit.text()),
        }