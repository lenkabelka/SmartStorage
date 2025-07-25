from PyQt6.QtWidgets import QGraphicsView
from PyQt6.QtGui import QWheelEvent, QPainter
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QTransform
from draggable_pixmap_item import DraggablePixmapItem


class ZoomableGraphicsView(QGraphicsView):
    resized = pyqtSignal()

    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.SmoothPixmapTransform
        )
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.SmartViewportUpdate)

        self.zoom_factor = 1.1  # более плавный зум
        self.current_zoom = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 10.0

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            zoom = self.zoom_factor if event.angleDelta().y() > 0 else 1 / self.zoom_factor
            new_zoom = self.current_zoom * zoom
            if self.min_zoom <= new_zoom <= self.max_zoom:
                self.scale(zoom, zoom)
                self.current_zoom = new_zoom
        else:
            super().wheelEvent(event)

    def reset_zoom(self):
        self.resetTransform()
        self.current_zoom = 1.0

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.resized.emit()


    def showEvent(self, event):
        super().showEvent(event)
        self.resized.emit()


    def keyPressEvent(self, event):
        focus_item = self.scene().focusItem()
        if isinstance(focus_item, DraggablePixmapItem):
            dx, dy = 0, 0
            if event.key() == Qt.Key.Key_Left:
                dx = -1
            elif event.key() == Qt.Key.Key_Right:
                dx = 1
            elif event.key() == Qt.Key.Key_Up:
                dy = -1
            elif event.key() == Qt.Key.Key_Down:
                dy = 1

            if dx != 0 or dy != 0:
                focus_item.moveBy(dx, dy)
        else:
            super().keyPressEvent(event)