from PyQt6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QScrollArea, QSizePolicy
from PyQt6.QtGui import QIcon, QGuiApplication
from PyQt6.QtCore import Qt
from thing import Thing
import image_container
from track_object_state import ObjectState


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

        if thing.thing_images:
            # Layout для изображений
            layout_images = QHBoxLayout()
            container_images = QWidget()
            container_images.setLayout(layout_images)
            container_images.adjustSize()

            scroll_for_images = QScrollArea()
            scroll_for_images.setWidgetResizable(True)
            scroll_for_images.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
            scroll_for_images.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll_for_images.setWidget(container_images)

            for item in thing.thing_images:
                image_widget = image_container.ImageContainer(item, container_images.contentsRect().height())
                image_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
                #image_widget.setMaximumHeight(scroll_for_images.height() - 40)
                #image_widget.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
                if not image_widget.space_image.state == ObjectState.DELETED:
                    layout_images.addWidget(image_widget)
            layout_images.addStretch()

            layout.addWidget(scroll_for_images)

        self.setLayout(layout)
