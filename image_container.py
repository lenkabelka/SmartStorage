from PyQt6.QtWidgets import QVBoxLayout, QWidget, QMenu, QLabel
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtCore import Qt, pyqtSignal

import enlarged_image_window as enlarged_image


class ImageContainer(QWidget):

    delete_image = pyqtSignal(object)

    def __init__(self, pixmap, height):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel()
        # тут у меня ссылка на тот же объект pixmap! -> могу передать в emit
        self.pixmap = pixmap
        label.setPixmap(pixmap.scaledToHeight(int(0.85 * height)))  # масштабируем изображение ???
        layout.addWidget(label)
        self.setLayout(layout)

        self.enlarged_window = None

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_enlarged_image()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        delete_action = menu.addAction("Удалить изображение")
        action = menu.exec(event.globalPos())
        if action == delete_action:

            self.delete_image.emit(self.pixmap)

            self.deleteLater()

    def open_enlarged_image(self):
        self.enlarged_window = enlarged_image.EnlargedImageWindow(self.pixmap)
        self.enlarged_window.show()