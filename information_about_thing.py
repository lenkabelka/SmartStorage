from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt6.QtGui import QIcon, QPixmap, QGuiApplication
from PyQt6.QtCore import Qt
from thing import Thing


class ThingInformation(QWidget):
    def __init__(self, thing: Thing):
        super().__init__()
        self.setWindowTitle("Информация о вещи")
        self.setWindowIcon(QIcon("icons/mini_logo.png"))

        screen_size = QGuiApplication.primaryScreen().size()
        screen_width = screen_size.width()
        screen_height = screen_size.height()
        width_coef = 0.3  # coefizient for width of Add Comment window
        height_coef = 0.4   #coefizient for height of Add Comment window
        self.setFixedSize(int(screen_width * width_coef), int(screen_height * height_coef))

        layout = QVBoxLayout()

        # Название вещи (выделено жирным)
        thing_name = QLabel(thing.name)
        thing_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thing_name.setStyleSheet("font-weight: bold; font-size: 22px;")
        layout.addWidget(thing_name)

        # Описание (если есть)
        thing_description = QLabel(thing.description or "Нет описания")
        thing_description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        thing_description.setStyleSheet("font-size: 16px;")
        thing_description.setWordWrap(True)
        layout.addWidget(thing_description)

        # Картинка (если указана и файл существует)
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        if thing.image:
            pixmap = QPixmap()
            pixmap.loadFromData(thing.image)

            if not pixmap.isNull():
                # Масштабируем под размер image_label с сохранением пропорций
                scaled_pixmap = pixmap.scaled(
                    image_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                image_label.setPixmap(scaled_pixmap)
            else:
                image_label.setText("Не удалось загрузить изображение.")
        else:
            image_label.setText("Изображение не указано.")

        layout.addWidget(image_label)

        self.setLayout(layout)
