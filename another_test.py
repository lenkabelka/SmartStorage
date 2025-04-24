from PyQt6.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QGraphicsItem, QVBoxLayout, QPushButton, QWidget
)
from PyQt6.QtGui import QPixmap, QImage, QKeyEvent, qAlpha
from PyQt6.QtCore import Qt, QRect
import sys

def crop_transparent_edges(pixmap: QPixmap) -> QPixmap:
    """Обрезает прозрачные края у картинки"""
    image = pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)

    left, top = image.width(), image.height()
    right, bottom = 0, 0

    for y in range(image.height()):
        for x in range(image.width()):
            if qAlpha(image.pixel(x, y)) > 0:
                left = min(left, x)
                right = max(right, x)
                top = min(top, y)
                bottom = max(bottom, y)

    if left > right or top > bottom:
        return QPixmap()  # Пустая картинка

    rect = QRect(left, top, right - left + 1, bottom - top + 1)
    return pixmap.copy(rect)


class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Добавление и закрепление картинок (обрезка фона)")
        self.resize(800, 640)

        self.view = QGraphicsView()
        self.scene = QGraphicsScene(self)
        self.view.setScene(self.scene)
        self.view.setSceneRect(0, 0, 800, 600)

        self.button = QPushButton("Add Picture")
        self.button.clicked.connect(self.add_next_item)

        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.addWidget(self.button)
        self.setLayout(layout)

        # Фоновая картинка (без столкновений)
        background = QPixmap("drawing.png")
        background_item = QGraphicsPixmapItem(background)
        background_item.setZValue(-1)  # Отправляем фон на самый задний план
        self.scene.addItem(background_item)

        self.items = []

    def add_next_item(self):
        # Загружаем и обрезаем прозрачные края
        pixmap = QPixmap("circle.png")
        cropped = crop_transparent_edges(pixmap)
        item = QGraphicsPixmapItem(cropped)
        print(item.shapeMode())
        item.setPos(50, 50)  # Начальная позиция
        self.scene.addItem(item)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyWidget()
    window.show()
    sys.exit(app.exec())