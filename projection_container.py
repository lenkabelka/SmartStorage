from PyQt6.QtWidgets import QWidget, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem, QVBoxLayout, QSizePolicy
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt
from typing import List


class ProjectionContainer(QWidget):
    def __init__(self, original_background, subprojections_list, container_width):
        super().__init__()

        #self.setFixedWidth(container_width)
        self.scene = QGraphicsScene()
        self.scene.setSceneRect(0, 0, int(0.85 * container_width), self.scene.height())
        self.view = QGraphicsView(self.scene)


        layout = QVBoxLayout()
        print("Я в классе!")

        # создаю копию background
        background_pixmap = original_background.pixmap()
        print("Я в классе_1!")
        self.background_copy = QGraphicsPixmapItem(background_pixmap)
        self.background_copy.setZValue(original_background.zValue())
        self.background_copy.setPos(original_background.pos())
        self.scene.addItem(self.background_copy)

        print("Я в классе_2!")
        print(f"subprojections_list: {subprojections_list}")

        # копии подпроекций
        for sub in subprojections_list:
            # if isinstance(sub.scaled_projection_pixmap, QGraphicsPixmapItem):
            #     pixmap = sub.scaled_projection_pixmap.pixmap()
            # else:
            #     print("Not a QGraphicsPixmapItem")
            print(f"sub: {sub}")
            print(f"sub_scaled_pixmap: {sub.scaled_projection_pixmap}")
            pixmap = sub.scaled_projection_pixmap.pixmap()
            print(f"sub_pixmap: {pixmap}")
            item_copy = QGraphicsPixmapItem(pixmap)
            print(f"x_pos: {sub.x_pos}")
            print(f"y_pos: {sub.y_pos}")
            item_copy.setPos(sub.x_pos, sub.y_pos)  # координаты сохраняются заранее
            self.scene.addItem(item_copy)

        layout.addWidget(self.view)
        self.setLayout(layout)
        print("Я в классе_3!")

        #self.view = QGraphicsView(self.scene)
        #self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        #self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        #self.view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        #self.view.setFixedHeight(20)  # или нужная тебе высота

        # масштабировать под фон
        self.view.setFixedWidth(self.width())
        self.view.fitInView(self.background_copy, Qt.AspectRatioMode.KeepAspectRatio)
        print("Я в классе_4!")