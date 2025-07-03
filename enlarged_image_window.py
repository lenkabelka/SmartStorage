from PyQt6.QtWidgets import QVBoxLayout, QWidget, QLabel
from PyQt6.QtGui import QIcon


class EnlargedImageWindow(QWidget):
    def __init__(self, pixmap):
        super().__init__()
        self.setWindowTitle("Увеличенное изображение")
        self.setWindowIcon(QIcon("icons/mini_logo.png"))
        layout = QVBoxLayout()
        label = QLabel()
        label.setPixmap(pixmap)
        layout.addWidget(label)
        self.setLayout(layout)

        self.resize(pixmap.width(), pixmap.height())