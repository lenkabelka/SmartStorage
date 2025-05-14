from PyQt6.QtWidgets import QVBoxLayout, QWidget, QLabel


class EnlargedImageWindow(QWidget):
    def __init__(self, pixmap):
        super().__init__()
        self.setWindowTitle("Увеличенное изображение")
        layout = QVBoxLayout()
        label = QLabel()
        label.setPixmap(pixmap)
        layout.addWidget(label)
        self.setLayout(layout)

        self.resize(pixmap.width(), pixmap.height())