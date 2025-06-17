from PyQt6.QtWidgets import (QGraphicsPixmapItem,
                             QGraphicsItem,
                             QGraphicsColorizeEffect,
                             QMenu
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

        self.setShapeMode(QGraphicsPixmapItem.ShapeMode.MaskShape)


        self.hover_color = QColor(0, 200, 255, 150)
        self.click_color = QColor(255, 0, 0, 150)
        self.setAcceptHoverEvents(True)
        self.is_editable = True

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.old_pos = self.pos()
        self.fixed = False

        self.item_id = id(self)

        self.background_pixmap = background_pixmap_item.pixmap()
        #self.path_1 = background_path

        self.path_1 = utils.get_path(utils.get_contours(self.background_pixmap)[0], utils.get_contours(self.background_pixmap)[1])
        self.path_2 = utils.get_path(utils.get_contours(self.original_pixmap)[0], utils.get_contours(self.original_pixmap)[1])


    # def paint(self, painter, option, widget=None):
    #     # Сначала рисуем само изображение
    #     super().paint(painter, option, widget)
    #
    #     # Рисуем контур background (path_1), с трансляцией в локальные координаты self
    #     if self.path_1:
    #         pen = QPen(Qt.GlobalColor.red)
    #         pen.setWidth(2)
    #         painter.setPen(pen)
    #         path_translated = self.path_1.translated(self.mapFromItem(self.parent_background_item, 0, 0))
    #         painter.drawPath(path_translated)
    #
    #     # Рисуем контур self (path_1)
    #     if self.path_2:
    #         pen_bg = QPen(Qt.GlobalColor.green)
    #         pen_bg.setWidth(2)
    #         pen_bg.setStyle(Qt.PenStyle.DashLine)
    #         painter.setPen(pen_bg)
    #         painter.drawPath(self.path_2)


    # @pyqtSlot(QPixmap)
    # def change_background_path(self, new_background_pixmap):
    #     self.background_pixmap = new_background_pixmap
    #     self.path_1 = utils.get_path(utils.get_contours(self.background_pixmap)[0],
    #                                  utils.get_contours(self.background_pixmap)[1])


    def update_path(self, new_background_pixmap_item):
        print(f"old_background: {self.background_pixmap}")
        self.background_pixmap = new_background_pixmap_item.pixmap()
        print(f"new_background: {self.background_pixmap}")

        self.path_1 = utils.get_path(utils.get_contours(self.background_pixmap)[0], utils.get_contours(self.background_pixmap)[1])
        self.path_2 = utils.get_path(utils.get_contours(self.original_pixmap)[0], utils.get_contours(self.original_pixmap)[1])

        print("klappt!")

    def mousePressEvent(self, event):
        from space import Space
        from thing import Thing
        self.drag_offset = event.pos()
        if event.button() == Qt.MouseButton.RightButton:
            menu = QMenu()
            freeze_action = menu.addAction("Зафиксировать")
            move_action = menu.addAction("Подвинуть")

            # Переменная delete_action может быть None, если ни один тип не подходит
            delete_item_action = None
            delete_subprojection_action = None
            delete_subprojections_action = None

            if isinstance(self.parent, Space):
                delete_item_action = menu.addAction("Удалить пространство")
            elif isinstance(self.parent, Thing):
                delete_item_action = menu.addAction("Удалить вещь")

            if isinstance(self.parent, Space):
                delete_subprojection_action = menu.addAction("Удалить эту проекцию пространства")
            elif isinstance(self.parent, Thing):
                delete_subprojection_action = menu.addAction("Удалить эту проекцию вещи")

            if isinstance(self.parent, Space):
                delete_subprojections_action = menu.addAction("Удалить все проекции этого пространства на всех развёртках")
            elif isinstance(self.parent, Thing):
                delete_subprojections_action = menu.addAction("Удалить все проекции этой вещи на всех развёртках")

            selected_action = menu.exec(event.screenPos())

            if selected_action == delete_subprojection_action:
                self.app_ref.delete_one_subprojection(self)
                #self.app_ref.update_tree_view()

            elif selected_action == delete_subprojections_action:
                self.app_ref.delete_all_subprojections(self)

            elif selected_action == freeze_action:
                self.freeze()

            elif selected_action == move_action:
                self.unfreeze()

        else:
            super().mousePressEvent(event)

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

                if utils.allow_movement(self.path_1, self.path_2, desired_pos.x(), desired_pos.y()):
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
            if utils.allow_movement(self.path_1, self.path_2, possible_pos.x(), possible_pos.y()):
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

            if utils.allow_movement(self.path_1, self.path_2, mid_point.x(), mid_point.y()):
                best_pos = mid_point
                left = mid
            else:
                right = mid

            if abs(right - left) < tolerance / (end - start).manhattanLength():
                break

        return best_pos