from PyQt6.QtWidgets import (QWidget, QLabel, QTextEdit, QPushButton, QVBoxLayout, QLineEdit, QApplication,
                             QMessageBox, QDialog, QFileDialog, QHBoxLayout, QCheckBox)
from PyQt6.QtGui import QFontMetrics, QFont, QGuiApplication, QRegularExpressionValidator, QIcon, QPixmap, QImage
from PyQt6.QtCore import Qt, QRegularExpression, pyqtSignal, QBuffer, QByteArray
import sys


class AddThing(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить вещь в пространство")
        self.setWindowIcon(QIcon("icons/mini_logo.png"))
        self.selected_file = ""

        # Создание виджетов
        self.name_edit = QLineEdit()
        self.description_edit = QTextEdit()

        self.image_label = QLabel("Нет изображения")


        # Переменная для хранения изображения
        self.image = None

        screen_size = QGuiApplication.primaryScreen().size()
        screen_width = screen_size.width()
        screen_height = screen_size.height()
        width_coef = 0.3    #coefizient for width of Add Comment window
        height_coef = 0.2   #coefizient for height of Add Comment window
        #self.image_label.setFixedSize(int(screen_width * width_coef), int(screen_height * height_coef))
        self.image_label.setFixedSize(self.width(), int(screen_height * height_coef))
        self.image_label.setStyleSheet("border: 1px solid gray;")

        self.load_button = QPushButton("Загрузить фотографию вещи")
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
        layout.addWidget(QLabel("*Название вещи:"))
        layout.addWidget(self.name_edit)
        layout.addWidget(QLabel("Описание вещи:"))
        layout.addWidget(self.description_edit)

        self.image_label.setMaximumWidth(self.width())
        layout.addWidget(QLabel("Фотография вещи:"))
        layout.addWidget(self.image_label)

        layout.addWidget(self.load_button)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)

        self.setLayout(layout)

        # Сигналы
        self.load_button.clicked.connect(self.load_image)
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

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
        # Возвращаем имя, описание, картинку
        return {
            "name": self.name_edit.text(),
            "description": self.description_edit.toPlainText() if self.description_edit.toPlainText() else None,
            "image": self.image if self.image else None
        }



# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     window = AddThing()
#     window.show()
#     sys.exit(app.exec())