from PyQt6.QtWidgets import QWidget, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem, QLabel, QVBoxLayout
from PyQt6.QtGui import QPixmap
from typing import List


class ProjectionContainer(QWidget):
    def __init__(self, background, subspace):
        super().__init__()

        layout = QVBoxLayout()

        self.scene = QGraphicsScene()
        self.view = QGraphicsView()
        self.view.setScene(self.scene)

        subspace: List[str, QGraphicsPixmapItem, List[QGraphicsPixmapItem, float, float]]
        background = subspace[1]
        label = QLabel(subspace[0])

        self.scene.addItem(background)
        for sub in subspace[2]:
            self.scene.addItem(sub[0])
            sub[0].setPos(sub[1], sub[2])


        layout.addWidget(self.scene)
        layout.addWidget(label)
