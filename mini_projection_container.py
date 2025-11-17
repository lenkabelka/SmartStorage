from PyQt6.QtWidgets import QWidget, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem, QVBoxLayout, QSizePolicy, \
    QMenu, QLabel, QGraphicsDropShadowEffect
from PyQt6.QtGui import QAction, QColor, QMouseEvent
from PyQt6.QtCore import Qt
from track_object_state import ObjectState


class ProjectionContainer(QWidget):
    def __init__(self, projection_to_save, app):
        super().__init__()

        self.app_ref = app

        self.saved_projection = projection_to_save
        self.projection = projection_to_save.copy()

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)

        self.label = QLabel(self.projection.projection_name)
        layout.addWidget(self.label)
        layout.addWidget(self.view)
        self.background_item = None

        if self.projection.scaled_projection_pixmap:
            self.background_item = self.projection.scaled_projection_pixmap
            self.scene.addItem(self.background_item)
            #self.background_item.setPos(self.projection.x_pos, self.projection.y_pos)
            #print(self.projection.x_pos, self.projection.y_pos)
            self.background_item.setZValue(self.projection.z_pos)
            print(self.projection.z_pos)


        if self.projection.sub_projections:
            for sub in self.projection.sub_projections:
                if not sub.scaled_projection_pixmap or sub.state == ObjectState.DELETED:
                    continue
                item = sub.scaled_projection_pixmap
                self.scene.addItem(item)
                item.setPos(sub.x_pos, sub.y_pos)
                item.setZValue(sub.z_pos)

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
        set_as_main_scene_action = QAction("Открыть, как главную проекцию", self)
        menu.addAction(delete_action)
        menu.addAction(set_as_main_scene_action)

        action = menu.exec(event.globalPos())
        if action == delete_action:
            if self.app_ref:
                self.app_ref.delete_mini_projection(self)
                #self.deleteLater()
        if action == set_as_main_scene_action:
            if self.app_ref:
                self.app_ref.set_mini_projection_on_main_scene(self)


    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.app_ref:
                self.app_ref.set_mini_projection_on_main_scene(self)


    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_view_size()


    def update_view_size(self):
        # максимально доступная ширина
        width = self.width()

        if self.background_item:
            background_pixmap = self.background_item.pixmap()
            aspect_ratio = background_pixmap.height() / background_pixmap.width()
            print(f"aspect_ratio: {aspect_ratio}")                                     #TODO почему печатается 3 раза?
            height = int(width * aspect_ratio)
            self.view.setFixedHeight(height)
            self.view.fitInView(self.background_item, Qt.AspectRatioMode.KeepAspectRatio)


    def update_scene(self, projection_to_change):
        try:
            self.scene.clear()

            self.projection = projection_to_change.copy()

            if self.projection.scaled_projection_pixmap:
                self.background_item = self.projection.scaled_projection_pixmap
                self.scene.addItem(self.background_item)
                #self.background_item.setPos(self.projection.x_pos, self.projection.y_pos)
                self.background_item.setZValue(self.projection.z_pos)

            if self.projection.sub_projections:
                for sub in self.projection.sub_projections:
                    if not sub.scaled_projection_pixmap or sub.state == ObjectState.DELETED:
                        continue
                    item = sub.scaled_projection_pixmap
                    self.scene.addItem(item)
                    item.setPos(sub.x_pos, sub.y_pos)
                    item.setZValue(sub.z_pos)

            self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
            self.view.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

            self.view.setSceneRect(self.scene.itemsBoundingRect())
            self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
            self.update_view_size()

            self.view.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            self.view.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        except Exception as e:
            print(e)


    def clear_highlights(self):
        for obj in self.scene.items():
            obj.setGraphicsEffect(None)


    def highlight(self, item):
        self.clear_highlights()
        effect = QGraphicsDropShadowEffect()
        effect.setBlurRadius(15)
        effect.setColor(QColor("red"))
        effect.setOffset(0, 0)
        item.setGraphicsEffect(effect)
