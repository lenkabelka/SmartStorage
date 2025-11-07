from PyQt6.QtWidgets import QVBoxLayout, QWidget, QLabel
from PyQt6.QtGui import QIcon, QPixmap, QGuiApplication
from PyQt6.QtCore import Qt, QSize
import utils


class EnlargedImageWindow(QWidget):
    def __init__(self, pixmap: QPixmap):
        super().__init__()
        self.setWindowTitle("Увеличенное изображение")
        self.setWindowIcon(QIcon(utils.resource_path("icons/mini_logo.png")))

        self.original_pixmap = pixmap

        self.label = QLabel()
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # вначале покажет картинку в её реальном размере
        self.label.resize(pixmap.width(), pixmap.height())
        # минимальный размер label
        self.label.setMinimumSize(pixmap.width(), pixmap.height())

        self.update_scaled_pixmap()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_scaled_pixmap()

    def update_scaled_pixmap(self):
        if not self.original_pixmap.isNull():
            target_size = self.label.size()
            scaled_pixmap = self.original_pixmap.scaled(
                target_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.label.setPixmap(scaled_pixmap)