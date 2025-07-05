from PyQt6.QtWidgets import QGraphicsScene, QGraphicsDropShadowEffect, QGraphicsPixmapItem
from PyQt6.QtGui import QColor
from PyQt6.QtCore import Qt, pyqtSignal
from draggable_pixmap_item import DraggablePixmapItem

class MainScene(QGraphicsScene):

    draggable_item_click = pyqtSignal(object)

    def __init__(self, app_ref, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.app_ref = app_ref  # если нужно
        # self.background = None  # если хочешь запомнить фон отдельно

    def mousePressEvent(self, event):
        item = self.itemAt(event.scenePos(), self.views()[0].transform())

        if type(item) == DraggablePixmapItem:
            self.focus_and_highlight(item)
        elif type(item) == QGraphicsPixmapItem:
            # Это фон — убираем подсветку
            self.clear_highlights()
        else:
            # Клик по пустому месту — тоже убираем подсветку
            self.clear_highlights()

        super().mousePressEvent(event)


    def mouseDoubleClickEvent(self, event):
        item = self.itemAt(event.scenePos(), self.views()[0].transform())

        if type(item) == DraggablePixmapItem:
            self.draggable_item_click.emit(item.parent)

        super().mouseDoubleClickEvent(event)


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
