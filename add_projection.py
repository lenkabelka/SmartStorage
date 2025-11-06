from PyQt6.QtWidgets import (QLabel, QTextEdit, QPushButton, QVBoxLayout, QLineEdit,
                             QMessageBox, QDialog, QFileDialog, QHBoxLayout, QCheckBox)
from PyQt6.QtGui import QGuiApplication, QRegularExpressionValidator, QIcon, QPixmap, QImage
from PyQt6.QtCore import Qt, QRegularExpression
from thing import Thing
from space import Space


class AddProjection(QDialog):

    def __init__(self, parent=None, projection_parent=None):
        super().__init__(parent)
        if isinstance(projection_parent, Space):
            self.setWindowTitle("Добавить проекцию пространства")
        elif isinstance(projection_parent, Thing):
            self.setWindowTitle("Добавить проекцию вещи")
        self.setWindowIcon(QIcon("icons/mini_logo.png"))
        self.selected_file = ""

        # Создание виджетов
        self.name_edit = QLineEdit()
        self.description_edit = QTextEdit()

        self.x_width = QLineEdit()
        self.y_height = QLineEdit()

        checkbox_layout = QHBoxLayout()
        checkbox_label = QLabel("Соотношение сторон изображения "
                                "в px соответствует реальному соотношению сторон проекции:")
        self.checkbox = QCheckBox()
        checkbox_layout.addWidget(checkbox_label)
        checkbox_layout.addWidget(self.checkbox)

        self.x_width.setText("1")
        reg_exp = QRegularExpression(r"^\d*\.?\d*$")
        validator = QRegularExpressionValidator(reg_exp)
        self.x_width.setValidator(validator)
        self.y_height.setText("1")
        self.y_height.setValidator(validator)

        self.image_label = QLabel("Нет изображения")

        screen_size = QGuiApplication.primaryScreen().size()
        screen_height = screen_size.height()
        height_coef = 0.2
        self.image_label.setFixedSize(self.width(), int(screen_height * height_coef))
        self.image_label.setStyleSheet("border: 1px solid gray;")

        self.load_button = QPushButton("Загрузить изображение")
        self.load_button.setAutoDefault(False)
        self.load_button.setDefault(False)
        self.ok_button = QPushButton("OK")
        self.ok_button.setAutoDefault(False)
        self.ok_button.setDefault(False)
        self.cancel_button = QPushButton("Отмена")
        self.cancel_button.setAutoDefault(False)
        self.cancel_button.setDefault(False)

        layout = QVBoxLayout()
        if isinstance(projection_parent, Space):
            layout.addWidget(QLabel("Имя проекции пространства*:"))
        elif isinstance(projection_parent, Thing):
            layout.addWidget(QLabel("Имя проекции вещи*:"))
        layout.addWidget(self.name_edit)
        if isinstance(projection_parent, Space):
            layout.addWidget(QLabel("Описание проекции пространства:"))
        elif isinstance(projection_parent, Thing):
            layout.addWidget(QLabel("Описание проекции вещи:"))
        layout.addWidget(self.description_edit)
        layout.addWidget(QLabel("Изображение*:"))
        layout.addWidget(self.image_label)
        layout.addLayout(checkbox_layout)

        layout_for_scales = QHBoxLayout()
        layout_for_scales.addWidget(QLabel("Размер проекции по x*:"))
        layout_for_scales.addWidget(self.x_width)
        layout_for_scales.addWidget(QLabel("Размер проекции по y*:"))
        layout_for_scales.addWidget(self.y_height)
        layout.addLayout(layout_for_scales)

        layout.addWidget(self.load_button)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        self.image = None

        self.load_button.clicked.connect(self.load_image)
        self.ok_button.clicked.connect(self.check_required_fields)
        self.cancel_button.clicked.connect(self.reject)
        self.x_width.returnPressed.connect(self.update_text_y)
        self.y_height.returnPressed.connect(self.update_text_x)


    def check_required_fields(self):
        """Проверяет обязательные поля и показывает предупреждения при их отсутствии."""
        if not self.check_size():
            return

        if not self.name_edit.text().strip():
            QMessageBox.warning(self, "Заполните обязательные поля",
                                "Пожалуйста, укажите название проекции!")
            return
        if not self.image:
            QMessageBox.warning(self, "Заполните обязательные поля",
                                "Пожалуйста, загрузите изображение проекции!")
            return
        else:
            self.accept()


    def update_text_y(self):
        if self.checkbox.isChecked():
            if not self.image:
                QMessageBox.warning(self, "Добавьте изображение проекции",
                                    "Для расчёта соотношения сторон необходимо "
                                    "вначале добавить изображение проекции!")
                return
            coef_sides_proportionality = self.image.width() / self.image.height()
            new_text_for_y = round((float(self.x_width.text()) / coef_sides_proportionality), 2)
            self.y_height.setText(str(new_text_for_y))

    def update_text_x(self):
        if self.checkbox.isChecked():
            if not self.image:
                QMessageBox.warning(self, "Добавьте изображение проекции",
                                    "Для расчёта соотношения сторон необходимо "
                                    "вначале добавить изображение проекции!")
                return
            coef_sides_proportionality = self.image.width() / self.image.height()
            new_text_for_x = round((float(self.y_height.text()) * coef_sides_proportionality), 2)
            self.x_width.setText(str(new_text_for_x))


    def set_image(self):
        scaled_image = self.image.scaled(
            self.image_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        pixmap = QPixmap.fromImage(scaled_image)
        self.image_label.setPixmap(pixmap)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)


    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выбрать изображение", "", "Images (*.png *.jpg *.bmp)"
        )
        if file_path:
            self.image = QImage(file_path)
            if self.image.isNull():
                QMessageBox.warning(self, "Ошибка", "Не удалось загрузить изображение.")
            else:
                self.set_image()


    def check_size(self):
        str_x = False
        str_y = False
        if self.x_width.text():
            for ch in self.x_width.text():
                if ch != "0" and ch != ".":
                    str_x = True

        if self.y_height.text():
            for ch in self.y_height.text():
                if ch != "0" and ch != ".":
                    str_y = True

        if str_x and str_y:
            return True
        else:
            QMessageBox.warning(self, "Некорректный размер", "Введите корректные размеры проекции!")
            return False


    def get_data(self):
        return {
            "name": self.name_edit.text(),
            "description": self.description_edit.toPlainText() if self.description_edit.toPlainText() else None,
            "image": self.image if self.image else None,
            "x_width": float(self.x_width.text()) if self.x_width and self.image and self.x_width.text() != "" else None,
            "y_height": float(self.y_height.text()) if self.y_height and self.image and self.y_height.text() != "" else None
        }