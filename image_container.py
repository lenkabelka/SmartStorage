from typing import Optional

from PyQt6.QtWidgets import QVBoxLayout, QWidget, QMenu, QLabel
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtCore import Qt, pyqtSignal
from typing import Optional

import enlarged_image_window as enlarged_image
import image


class ImageContainer(QWidget):

    delete_image = pyqtSignal(object)

    def __init__(self, space_image, height):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel()
        # тут у меня ссылка на тот же объект pixmap! -> могу передать в emit
        self.space_image: Optional[image.SpaceImage] | None = space_image
        #self.pixmap = pixmap
        label.setPixmap(self.space_image.image.scaledToHeight(int(0.75 * height)))  # масштабируем изображение ???
        layout.addWidget(label)
        self.setLayout(layout)

        self.enlarged_window = None

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.open_enlarged_image()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        delete_action = menu.addAction("Удалить эту фотографию пространства")
        action = menu.exec(event.globalPos())
        if action == delete_action:

            self.delete_image.emit(self.space_image)

            self.deleteLater()

    def open_enlarged_image(self):
        self.enlarged_window = enlarged_image.EnlargedImageWindow(self.space_image.image)
        self.enlarged_window.show()