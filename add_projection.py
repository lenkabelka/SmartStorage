import math

from PyQt6.QtWidgets import (QWidget, QLabel, QTextEdit, QPushButton, QVBoxLayout, QLineEdit,
                             QMessageBox, QDialog, QFileDialog, QHBoxLayout, QCheckBox)
from PyQt6.QtGui import QFontMetrics, QFont, QGuiApplication, QRegularExpressionValidator, QIcon, QPixmap, QImage
from PyQt6.QtCore import Qt, QRegularExpression, pyqtSignal, QBuffer, QByteArray
import sys


class AddProjection(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить проекцию пространства")
        self.selected_file = ""

        # Создание виджетов
        self.name_edit = QLineEdit()
        self.description_edit = QTextEdit()

        # Добавлены два QLineEdit для ввода коэффициентов масштабирования
        self.x_sm = QLineEdit()
        self.y_sm = QLineEdit()

        checkbox_layout = QHBoxLayout()
        checkbox_label = QLabel("Соотношение сторон изображения в px соответствует соотношению сторон пространства в сантиметрах:")
        self.checkbox = QCheckBox()
        checkbox_layout.addWidget(checkbox_label)
        checkbox_layout.addWidget(self.checkbox)

        # Установка начальных значений (например, 1 для коэффициента масштаба)
        self.x_sm.setText("1")
        reg_exp = QRegularExpression(r"^\d*\.?\d*$")
        validator = QRegularExpressionValidator(reg_exp)
        self.x_sm.setValidator(validator)
        self.y_sm.setText("1")
        self.y_sm.setValidator(validator)

        self.image_label = QLabel("Нет изображения")

        self.x_scale = None
        self.y_scale = None

        screen_size = QGuiApplication.primaryScreen().size()
        screen_width = screen_size.width()
        screen_height = screen_size.height()
        width_coef = 0.3    #coefizient for width of Add Comment window
        height_coef = 0.2   #coefizient for height of Add Comment window
        self.image_label.setFixedSize(int(screen_width * width_coef), int(screen_height * height_coef))
        self.image_label.setStyleSheet("border: 1px solid gray;")

        self.load_button = QPushButton("Загрузить картинку")
        self.load_button.setAutoDefault(False)
        self.load_button.setDefault(False)
        self.ok_button = QPushButton("OK")
        self.ok_button.setAutoDefault(False)
        self.ok_button.setDefault(False)
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.setAutoDefault(False)
        self.cancel_button.setDefault(False)

        # Layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Имя проекции пространства:"))
        layout.addWidget(self.name_edit)
        layout.addWidget(QLabel("Описание проекции пространства:"))
        layout.addWidget(self.description_edit)

        layout.addWidget(QLabel("Картинка:"))
        layout.addWidget(self.image_label)

        # Добавление этих полей в layout
        layout.addLayout(checkbox_layout)

        layout_for_scales = QHBoxLayout()

        layout_for_scales.addWidget(QLabel("Размер пространства по x, в см:"))
        layout_for_scales.addWidget(self.x_sm)
        layout_for_scales.addWidget(QLabel("Размер пространства по y, в см:"))
        layout_for_scales.addWidget(self.y_sm)

        layout.addLayout(layout_for_scales)

        layout.addWidget(self.load_button)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Переменная для хранения изображения
        self.image = None

        # Сигналы
        self.load_button.clicked.connect(self.load_image)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.x_sm.returnPressed.connect(self.update_text_y)
        self.y_sm.returnPressed.connect(self.update_text_x)


    def update_text_y(self):
        if self.checkbox.isChecked():
            print("Punkt_1")
            if not self.image:
                print("Punkt_2")
                QMessageBox.warning(self, "Добавьте проекцию пространства",
                                    "Для расчёта соотношения сторон необходимо"
                                    " вначале добавить проекцию пространства!")
                return
            else:
                coef_sides_proportionality = self.image.width() / self.image.height()
                print(coef_sides_proportionality)
                new_text_for_y = round((float(self.x_sm.text()) / coef_sides_proportionality), 2)
                print(new_text_for_y)
                self.y_sm.setText(str(new_text_for_y))
        else:
            return


    def update_text_x(self):
        if self.checkbox.isChecked():
            print("Punkt_1")
            if not self.image:
                print("Punkt_2")
                QMessageBox.warning(self, "Добавьте проекцию пространства",
                                    "Для расчёта соотношения сторон необходимо"
                                    " вначале добавить проекцию пространства!")
                return
            else:
                coef_sides_proportionality = self.image.width() / self.image.height()
                print(coef_sides_proportionality)
                new_text_for_x = round((float(self.y_sm.text()) * coef_sides_proportionality), 2)
                print(new_text_for_x)
                self.x_sm.setText(str(new_text_for_x))
        else:
            return


    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выбрать изображение", "", "Images (*.png *.jpg *.bmp)"
        )
        if file_path:
            self.image = QImage(file_path)

            if self.image.isNull():
                QMessageBox.warning(self, "Ошибка", "Не удалось загрузить изображение.")
            else:
                # Масштабирование с сохранением пропорций
                scaled_image = self.image.scaled(
                    self.image_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                pixmap = QPixmap.fromImage(scaled_image)
                # Центрируем изображение в QLabel
                self.image_label.setPixmap(pixmap)
                self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)


    def get_data(self):
        # Возвращаем имя, описание, картинку в байтах и коэффициенты масштабирования
        return {
            "name": self.name_edit.text(),
            "description": self.description_edit.toPlainText(),
            "image": self.image if self.image else None,
            "x_sm": float(self.x_sm.text()) if self.image else None,
            "y_sm": float(self.y_sm.text()) if self.image else None
        }