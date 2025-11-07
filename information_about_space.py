from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QScrollArea, QSizePolicy
from PyQt6.QtGui import QIcon, QGuiApplication
from PyQt6.QtCore import Qt
from space import Space
import image_container
from track_object_state import ObjectState
import utils


class SpaceInformation(QWidget):
    def __init__(self, sp: Space):
        super().__init__()
        self.setWindowTitle("Информация о вещи")
        self.setWindowIcon(QIcon(utils.resource_path("icons/mini_logo.png")))

        screen_size = QGuiApplication.primaryScreen().size()
        screen_width = screen_size.width()
        screen_height = screen_size.height()
        width_coef = 0.3  # coefizient for width of Add Comment window
        height_coef = 0.4   #coefizient for height of Add Comment window
        self.setFixedSize(int(screen_width * width_coef), int(screen_height * height_coef))

        layout = QVBoxLayout()

        # Название вещи (выделено жирным)
        space_name = QLabel(sp.name)
        space_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        space_name.setStyleSheet("font-weight: bold; font-size: 22px;")
        layout.addWidget(space_name)

        # Описание (если есть)
        space_description = QLabel(sp.description or "Нет описания")
        space_description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        space_description.setStyleSheet("font-size: 16px;")
        space_description.setWordWrap(True)
        layout.addWidget(space_description)


        self.setLayout(layout)