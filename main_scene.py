from PyQt6.QtWidgets import QGraphicsScene, QGraphicsDropShadowEffect, QGraphicsPixmapItem, QGraphicsItem
from PyQt6.QtGui import QColor
from PyQt6.QtCore import pyqtSignal
from draggable_pixmap_item import DraggablePixmapItem

class MainScene(QGraphicsScene):

    draggable_item_click = pyqtSignal(object)

    def __init__(self, app_ref, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app_ref = app_ref


    def mousePressEvent(self, event):
        item = self.itemAt(event.scenePos(), self.views()[0].transform())

        if type(item) == DraggablePixmapItem:
            self.draggable_item_click.emit(item.parent)
            super().mousePressEvent(event)
            #self.focus_and_highlight(item)
            try:
                # тут item это объект типа DraggablePixmapItem,
                # у него есть аттрибут parent (вещь Thing или подпространство Space)
                self.app_ref.highlight_subprojections_on_mini_projections(item.parent)
            except Exception as e:
                print(f"Ошибка при вызове highlight_subprojections: {e}")

        elif type(item) == QGraphicsPixmapItem:
            # Это фон — убираем подсветку
            self.clear_highlights()
            self.app_ref.highlight_subprojections_on_mini_projections(None)

        else:
            # Клик по пустому месту — тоже убираем подсветку
            self.clear_highlights()
            self.app_ref.highlight_subprojections_on_mini_projections(None)




    def update_items_movable_flag(self, item_to_update=None):
        """Выставляет всем DraggablePixmapItem флаг ItemIsMovable в зависимости от прав пользователя."""
        can_edit = self.app_ref.access_manager.can_edit(self.app_ref.parent_space)

        print(f"can_edit: {can_edit}")

        if item_to_update:
            if isinstance(item_to_update, DraggablePixmapItem):
                # Установим флаг перемещения
                item_to_update.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, can_edit)

                # # Получим все установленные флаги
                # flags = item_to_update.flags()
                #
                # # Переберём все возможные флаги и выведем включённые для элементов DraggablePixmapItem
                # enabled_flags = [f for f in QGraphicsItem.GraphicsItemFlag if flags & f]
                # print("Enabled flags for DraggablePixmapItem:")
                # for f in enabled_flags:
                #     print(" -", f.name)

        else:
            for item in self.items():
                if isinstance(item, DraggablePixmapItem):
                    # Установим флаг перемещения
                    item.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, can_edit)

                    # # Получим все установленные флаги
                    # flags = item.flags()
                    #
                    # # Переберём все возможные флаги и выведем включённые для элементов DraggablePixmapItem
                    # enabled_flags = [f for f in QGraphicsItem.GraphicsItemFlag if flags & f]
                    # print("Enabled flags for DraggablePixmapItem:")
                    # for f in enabled_flags:
                    #     print(" -", f.name)


    # def mouseDoubleClickEvent(self, event):
    #     item = self.itemAt(event.scenePos(), self.views()[0].transform())
    #
    #     if type(item) == DraggablePixmapItem:
    #         self.draggable_item_click.emit(item.parent)
    #
    #     super().mouseDoubleClickEvent(event)


    def clear_highlights(self):
        for obj in self.items():
            if isinstance(obj, DraggablePixmapItem):
                obj.setGraphicsEffect(None)
                obj.clearFocus()


    def focus_and_highlight(self, item):
        self.clear_highlights()
        item.setFocus()
        effect = QGraphicsDropShadowEffect()
        effect.setBlurRadius(15)
        effect.setColor(QColor("red"))
        effect.setOffset(0, 0)
        item.setGraphicsEffect(effect)