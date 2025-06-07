from PyQt6.QtWidgets import QWidget, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem, QVBoxLayout, QSizePolicy, \
    QMenu, QLabel
from PyQt6.QtGui import QAction, QPixmap
from PyQt6.QtCore import Qt
from track_object_state import ObjectState


class ProjectionContainer(QWidget):
    def __init__(self, projection_to_save, app):
        super().__init__()

        self.app_ref = app
        self.saved_projection = projection_to_save
        self.sub_projections_list = None
        if projection_to_save.sub_projections:
            self.sub_projections_list = projection_to_save.sub_projections

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)

        label = QLabel(self.saved_projection.projection_name)
        layout.addWidget(label)
        layout.addWidget(self.view)

        #self.background_pixmap = QPixmap.fromImage(projection_to_save.projection_image)
        #self.background_item = QGraphicsPixmapItem(self.background_pixmap)
        self.background_pixmap = projection_to_save.scaled_projection_pixmap

        self.background_item = QGraphicsPixmapItem(self.background_pixmap)
        min_z = min((item.zValue() for item in self.scene.items()), default=0)
        self.background_item.setZValue(min_z - 1)  # Отправляем фон на самый задний план
        self.scene.addItem(self.background_item)

        if self.sub_projections_list:
            for sub in self.sub_projections_list:
                if sub.state != ObjectState.DELETED:
                    pixmap = sub.scaled_projection_pixmap.pixmap()
                    item_copy = QGraphicsPixmapItem(pixmap)
                    item_copy.setPos(sub.x_pos, sub.y_pos)
                    self.scene.addItem(item_copy)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.update_view_size()

        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        rect = self.background_item.boundingRect()
        self.scene.setSceneRect(rect)

        self.setLayout(layout)


    def contextMenuEvent(self, event):
        menu = QMenu(self)
        delete_action = QAction("Удалить эту проекцию", self)
        menu.addAction(delete_action)

        action = menu.exec(event.globalPos())
        if action == delete_action:
            if self.app_ref:
                self.app_ref.delete_mini_projection(self)
            self.deleteLater()


    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_view_size()


    def update_view_size(self):
        # максимально доступная ширина
        width = self.width()

        if not self.background_pixmap.isNull():
            aspect_ratio = self.background_pixmap.height() / self.background_pixmap.width()
            height = int(width * aspect_ratio)
            self.view.setFixedHeight(height)
            self.view.fitInView(self.background_item, Qt.AspectRatioMode.KeepAspectRatio)


    def update_scene(self, projection_to_change):
        self.scene.clear()
        self.sub_projections_list = None
        if projection_to_change.sub_projections:
            self.sub_projections_list = projection_to_change.sub_projections

        # self.background_pixmap = QPixmap.fromImage(projection_to_change.projection_image)
        # self.background_item = QGraphicsPixmapItem(self.background_pixmap)

        self.background_pixmap = projection_to_change.scaled_projection_pixmap
        self.background_item = QGraphicsPixmapItem(self.background_pixmap)
        min_z = min((item.zValue() for item in self.scene.items()), default=0)
        self.background_item.setZValue(min_z - 1)  # Отправляем фон на самый задний план
        self.scene.addItem(self.background_item)

        if self.sub_projections_list:
            for sub in self.sub_projections_list:
                if sub.state != ObjectState.DELETED:
                    pixmap = sub.scaled_projection_pixmap.pixmap()
                    item_copy = QGraphicsPixmapItem(pixmap)
                    item_copy.setPos(sub.x_pos, sub.y_pos)
                    self.scene.addItem(item_copy)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.view.setSceneRect(self.scene.itemsBoundingRect())
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.update_view_size()

        self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
