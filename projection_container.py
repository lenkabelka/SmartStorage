from PyQt6.QtWidgets import QWidget, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem, QVBoxLayout, QSizePolicy
from PyQt6.QtCore import Qt


class ProjectionContainer(QWidget):
    def __init__(self, original_background, projection_to_save):
        super().__init__()

        sub_projections_list = None
        if projection_to_save.sub_projections:
            sub_projections_list = projection_to_save.sub_projections

        self.saved_projection = projection_to_save

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)

        layout.addWidget(self.view)

        # копия background
        background_pixmap = original_background.pixmap()

        self.background_copy = QGraphicsPixmapItem(background_pixmap)
        self.background_copy.setZValue(original_background.zValue())
        self.background_copy.setPos(original_background.pos())
        self.scene.addItem(self.background_copy)

        # копии подпроекций
        if sub_projections_list:
            for sub in sub_projections_list:
                pixmap = sub.scaled_projection_pixmap.pixmap()
                item_copy = QGraphicsPixmapItem(pixmap)
                item_copy.setPos(sub.x_pos, sub.y_pos)  # координаты сохраняются заранее
                self.scene.addItem(item_copy)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.update_view_size()

        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        rect = self.background_copy.boundingRect()
        self.scene.setSceneRect(rect)

        self.setLayout(layout)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_view_size()

    def update_view_size(self):
        # максимально доступная ширина
        width = self.width()

        if self.background_copy is not None:
            pixmap_background = self.background_copy.pixmap()
            if not pixmap_background.isNull():
                aspect_ratio = pixmap_background.height() / pixmap_background.width()
                height = int(width * aspect_ratio)
                self.view.setFixedHeight(height)
                self.view.fitInView(self.background_copy, Qt.AspectRatioMode.KeepAspectRatio)


    def update_scene(self, original_background, subprojections_list=None):
        self.scene.clear()

        background_pixmap = original_background.pixmap()

        self.background_copy = QGraphicsPixmapItem(background_pixmap)
        self.background_copy.setZValue(original_background.zValue())
        self.background_copy.setPos(original_background.pos())
        self.scene.addItem(self.background_copy)

        if subprojections_list:
            for sub in subprojections_list:
                pixmap = sub.scaled_projection_pixmap.pixmap()
                item_copy = QGraphicsPixmapItem(pixmap)
                item_copy.setPos(sub.x_pos, sub.y_pos)
                self.scene.addItem(item_copy)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.view.setSceneRect(self.scene.itemsBoundingRect())  # здесь!
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.update_view_size()

        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
