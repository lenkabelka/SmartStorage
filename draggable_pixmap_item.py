from PyQt6.QtWidgets import(
    QGraphicsPixmapItem,
    QGraphicsItem,
    QGraphicsColorizeEffect,
    QMenu, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QComboBox, QWidgetAction
)
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, QPointF
import utils as utils
import math


class DraggablePixmapItem(QGraphicsPixmapItem):
    def __init__(self, pixmap, app, background_pixmap_item, parent):
        super().__init__(pixmap)
        self.app_ref = app
        self.drag_offset = QPointF()
        self.binary_search = "version_1"
        self.original_pixmap = pixmap
        self.parent = parent

        from thing import Thing
        if parent is not None and isinstance(parent, Thing):
            self.parent_id = parent.id_thing  # это нужно, чтобы "подсветить" развертки вещи на мини-проекциях,
                                              # при выборе "показать вещь в пространстве"

        # для четкого изображения
        self.setTransformationMode(Qt.TransformationMode.SmoothTransformation)

        self.setShapeMode(QGraphicsPixmapItem.ShapeMode.MaskShape)

        self.hover_color = QColor(0, 200, 255, 150)
        self.click_color = QColor(255, 0, 0, 150)
        self.setAcceptHoverEvents(True)
        self.is_editable = True
        self.setAcceptHoverEvents(True)
        self.old_pos = self.pos()
        self.fixed = False

        self.item_id = id(self)

        self.background_pixmap = background_pixmap_item.pixmap()

        self.path_background = utils.get_path(utils.get_contours(self.background_pixmap)[0], utils.get_contours(self.background_pixmap)[1])
        self.path_subprojection = utils.get_path(utils.get_contours(self.original_pixmap)[0], utils.get_contours(self.original_pixmap)[1])

        # нужно для проверки столкновения с прозрачной областью, смотри функцию itemChange
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        # нужно для возможности двигать элемент стрелками
        self.setFlag(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsFocusable)


    def update_path(self, new_background_pixmap_item=None):
        #print(f"old_background: {self.background_pixmap}")
        if new_background_pixmap_item is not None:
            self.background_pixmap = new_background_pixmap_item.pixmap()
        #print(f"new_background: {self.background_pixmap}")

        # контур развертки
        self.path_background = utils.get_path(utils.get_contours(self.background_pixmap)[0], utils.get_contours(self.background_pixmap)[1])
        # контур подразвертки
        self.path_subprojection = utils.get_path(utils.get_contours(self.original_pixmap)[0], utils.get_contours(self.original_pixmap)[1])


    def mousePressEvent(self, event):
        from space import Space
        from thing import Thing
        self.drag_offset = event.pos()

        try:

            if event.button() == Qt.MouseButton.RightButton:
                menu = QMenu()
                freeze_action = menu.addAction("Зафиксировать")
                move_action = menu.addAction("Подвинуть")

                # Переменная delete_action может быть None, если ни один тип не подходит
                delete_item_action = None
                delete_subprojection_action = None
                delete_subprojections_action = None
                show_information_action = None
                set_above_other_subprojection = None

                if isinstance(self.parent, Space):
                    delete_item_action = menu.addAction("Удалить пространство")
                    delete_subprojection_action = menu.addAction("Удалить эту проекцию пространства")
                    delete_subprojections_action = menu.addAction(
                        "Удалить все проекции этого пространства на всех развёртках")
                    show_information_action = menu.addAction("Показать информацию о подпространстве")
                    menu.addAction("Посмотреть все вещи в пространстве",
                                   lambda: self.app_ref.show_all_things_in_space(self.parent))
                elif isinstance(self.parent, Thing):
                    delete_item_action = menu.addAction("Удалить вещь")
                    delete_subprojection_action = menu.addAction("Удалить эту проекцию вещи")
                    delete_subprojections_action = menu.addAction("Удалить все проекции этой вещи на всех развёртках")
                    show_information_action = menu.addAction("Показать информацию о вещи")

                change_information_action = menu.addAction("Изменить")


                # Контейнер для текста и комбобокса
                move_to_another_z_position = QWidgetAction(menu)

                container = QWidget()
                layout = QHBoxLayout(container)
                layout.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                #layout.setContentsMargins(6, 2, 6, 2)  # аккуратные отступы

                # Текст как часть пункта меню
                # QLabel не обязательный, можно просто ComboBox
                combo = QComboBox()

                # Заполняем ComboBox
                if self.app_ref.parent_space is not None and self.app_ref.parent_space.current_projection is not None:
                    if self.app_ref.parent_space.current_projection.sub_projections:
                        for item in self.app_ref.parent_space.current_projection.sub_projections:
                            parent = item.reference_to_parent_space or item.reference_to_parent_thing
                            if parent is not None:
                                combo.addItem(parent.name)

                # Добавляем COMBO в layout (без Label, как ты и хочешь)
                layout.addWidget(combo)

                # Устанавливаем контейнер в QAction
                move_to_another_z_position.setDefaultWidget(container)
                set_above_other_subprojection = menu.addAction("Поместить поверх подразвертки:")  # обычный текст (без ComboBox)
                menu.addAction(move_to_another_z_position)  # ComboBox как следующий пункт



                selected_action = menu.exec(event.screenPos())

                if selected_action == set_above_other_subprojection:
                    self.app_ref.find_projection(self)
                    self.app_ref.move_draggable_to_another_z_position(self, combo.currentText())

                elif selected_action == change_information_action:
                    self.app_ref.change_thing_or_subspace_subprojection(self)

                elif selected_action == delete_subprojection_action:
                    self.app_ref.delete_one_subprojection(self)

                elif selected_action == delete_subprojections_action:
                    self.app_ref.delete_all_subprojections(self)

                elif selected_action == freeze_action:
                    self.freeze()

                elif selected_action == move_action:
                    self.unfreeze()

                elif selected_action == delete_item_action:
                    if isinstance(self.parent, Space):
                        self.app_ref.delete_subspace(self.parent)
                    elif isinstance(self.parent, Thing):
                        self.app_ref.delete_thing(self.parent)

                elif selected_action == show_information_action:
                    if isinstance(self.parent, Thing):
                        self.app_ref.show_thing_information(self.parent)
                    elif isinstance(self.parent, Space):
                        self.app_ref.show_space_information(self.parent)

            else:
                super().mousePressEvent(event)

        except Exception as e:
            print(f"Unexpected error: {e}")


    def mouseMoveEvent(self, event):
        new_scene_pos = event.scenePos() - self.drag_offset
        self.setPos(new_scene_pos)
        super().mouseMoveEvent(event)


    def hoverEnterEvent(self, event):
        if not self.is_editable:
            effect = QGraphicsColorizeEffect()
            effect.setColor(QColor("green"))
            self.setGraphicsEffect(effect)


    def hoverLeaveEvent(self, event):
        if not self.is_editable:
            self.setGraphicsEffect(None)


    def freeze(self):
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.fixed = True
        self.setGraphicsEffect(None)


    def unfreeze(self):
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.fixed = False


    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange and self.scene():
            if self.fixed:
                return self.pos()
            else:
                current_pos = self.pos()
                desired_pos = value

                if utils.allow_movement(self.path_background, self.path_subprojection, desired_pos.x(), desired_pos.y()):
                    return value

                if self.binary_search == "version_1":
                    new_pos = self.binary_search_position_1(current_pos, desired_pos)
                    return new_pos if new_pos else current_pos
                if self.binary_search == "version_2":
                    new_pos = self.binary_search_position_2(current_pos, desired_pos)
                    return new_pos if new_pos else current_pos

        return super().itemChange(change, value)


    def binary_search_position_1(self, start: QPointF, end: QPointF):
        best_pos = None
        while True:
            possible_pos = (start + end) / 2
            if utils.allow_movement(self.path_background, self.path_subprojection, possible_pos.x(), possible_pos.y()):
                best_pos = possible_pos
                start = possible_pos
            else:
                end = possible_pos

            dx = end.x() - start.x()
            dy = end.y() - end.y()
            distance = math.hypot(dx, dy)
            if  distance < 0.5:
                break

        return best_pos


    def binary_search_position_2(self, start: QPointF, end: QPointF, max_iter=20, tolerance=0.5):
        left = 0.0
        right = 1.0
        best_pos = None

        for _ in range(max_iter):
            mid = (left + right) / 2.0
            mid_point = QPointF(
                start.x() + (end.x() - start.x()) * mid,
                start.y() + (end.y() - start.y()) * mid
            )

            if utils.allow_movement(self.path_background, self.path_subprojection, mid_point.x(), mid_point.y()):
                best_pos = mid_point
                left = mid
            else:
                right = mid

            if abs(right - left) < tolerance / (end - start).manhattanLength():
                break

        return best_pos