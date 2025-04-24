import sys
from PyQt6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QGraphicsPixmapItem, QGraphicsPolygonItem
from PyQt6.QtGui import QPixmap, QBrush, QColor, QPolygonF
from PyQt6.QtCore import QPointF, Qt, QTimer

class ClickablePolygon(QGraphicsPolygonItem):
    def __init__(self):
        super().__init__()
        self.polygon = QPolygonF()
        self.setPolygon(self.polygon)
        self.default_color = QColor(0, 255, 0, 100)
        self.hover_color = QColor(0, 200, 255, 150)
        self.click_color = QColor(255, 0, 0, 150)
        self.setBrush(QBrush(self.default_color))
        self.setAcceptHoverEvents(True)
        self.is_editable = True


    def add_point(self, point):
        if self.is_editable:
            self.polygon.append(point)
            self.setPolygon(self.polygon)


    def finish_polygon(self):
        self.is_editable = False
        print("Polygon is finished!")


    def hoverEnterEvent(self, event):
        if not self.is_editable:
            self.setBrush(QBrush(self.hover_color))


    def hoverLeaveEvent(self, event):
        if not self.is_editable:
            self.setBrush(QBrush(self.default_color))


    def mousePressEvent(self, event):
        if not self.is_editable:
            self.setBrush(QBrush(self.click_color))
            QTimer.singleShot(200, lambda: self.setBrush(QBrush(self.hover_color)))
            print("Polygon is clicked!")


class ImageWithPolygon(QGraphicsPixmapItem):
    def __init__(self, pixmap, polygon_item):
        super().__init__(pixmap)
        self.polygon_item = polygon_item


    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.polygon_item.add_point(event.scenePos())
            print(f"The point is added: {event.scenePos().x()}, {event.scenePos().y()}")
        elif event.button() == Qt.MouseButton.RightButton:
            self.polygon_item.finish_polygon()


# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#
#     scene = QGraphicsScene()
#
#     pixmap = QPixmap("space.png")
#     polygon_item = ClickablePolygon()
#     pixmap_item = ImageWithPolygon(pixmap, polygon_item)
#
#     scene.addItem(pixmap_item)
#     scene.addItem(polygon_item)
#
#     view = QGraphicsView(scene)
#
#     def finish_on_key(event):
#         if event.key() == Qt.Key.Key_Return:
#             polygon_item.finish_polygon()
#
#     view.keyPressEvent = finish_on_key
#     view.setScene(scene)
#     view.show()
#
#     sys.exit(app.exec())