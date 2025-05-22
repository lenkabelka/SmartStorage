from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QGraphicsScene,
    QGraphicsView, QGraphicsPixmapItem
)
from PyQt6.QtGui import QPixmap, QWheelEvent, QPainter
from PyQt6.QtCore import Qt
import sys


class ZoomableGraphicsView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        self.setTransformationAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorUnderMouse)
        self.zoom_factor = 1.15
        self.current_zoom = 1.0
        self.min_zoom = 0.1
        self.max_zoom = 10.0

    def wheelEvent(self, event: QWheelEvent):
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:  # Ctrl + Scroll
            zoom = self.zoom_factor if event.angleDelta().y() > 0 else 1 / self.zoom_factor
            new_zoom = self.current_zoom * zoom
            if self.min_zoom <= new_zoom <= self.max_zoom:
                self.scale(zoom, zoom)
                self.current_zoom = new_zoom
        else:
            super().wheelEvent(event)