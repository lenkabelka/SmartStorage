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
        self.sub_projections_list = None
        if projection_to_save.sub_projections:
            self.sub_projections_list = projection_to_save.sub_projections

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)

        self.projection_name = self.saved_projection.projection_name

        self.label = QLabel(self.projection_name)
        layout.addWidget(self.label)
        layout.addWidget(self.view)

        # Копия current_projection:
        self.background_item = QGraphicsPixmapItem(self.saved_projection.original_pixmap)
        self.scene.addItem(self.background_item)

        if self.sub_projections_list:
            for sub in self.sub_projections_list:
                if sub.state != ObjectState.DELETED:
                    item_copy = QGraphicsPixmapItem(sub.original_pixmap)
                    item_copy.setPos(sub.x_pos, sub.y_pos)
                    item_copy.setZValue(sub.z_pos)

                    if sub.reference_to_parent_space:
                        item_copy.parent = sub.reference_to_parent_space  # чтобы потом найти её на всех сценах и подсветить
                    else:
                        item_copy.parent = sub.reference_to_parent_thing
                        item_copy.thing_id = sub.reference_to_parent_thing.id_thing  # чтобы потом найти вешь на всех сценах и подсветить

                    self.scene.addItem(item_copy)

        min_z = min((item.zValue() for item in self.scene.items()), default=0)
        self.background_item.setZValue(min_z - 1)  # Отправляем фон на самый задний план

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


    def update_mini_projection_name(self, projection_to_change):
        self.label.setText(projection_to_change.projection_name)


    def update_scene(self, projection_to_change):
        try:
            self.scene.clear()
            self.sub_projections_list = None
            if projection_to_change.sub_projections:
                self.sub_projections_list = projection_to_change.sub_projections

            self.background_item = QGraphicsPixmapItem(projection_to_change.original_pixmap)
            self.scene.addItem(self.background_item)

            if self.sub_projections_list:
                for sub in self.sub_projections_list:
                    if sub.state != ObjectState.DELETED:
                        item_copy = QGraphicsPixmapItem(sub.original_pixmap)
                        item_copy.setPos(sub.x_pos, sub.y_pos)
                        item_copy.setZValue(sub.z_pos)

                        if sub.reference_to_parent_space:
                            item_copy.parent = sub.reference_to_parent_space  # чтобы потом найти её на всех сценах и подсветить
                        else:
                            item_copy.parent = sub.reference_to_parent_thing
                            item_copy.thing_id = sub.reference_to_parent_thing.id_thing  # чтобы потом найти вещь на всех сценах и подсветить

                        self.scene.addItem(item_copy)

            min_z = min((item.zValue() for item in self.scene.items()), default=0)
            self.background_item.setZValue(min_z - 1)  # Отправляем фон на самый задний план

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
