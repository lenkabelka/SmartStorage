from PyQt6.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QGraphicsItem, QVBoxLayout, QPushButton, QWidget, QGraphicsColorizeEffect, QMenu
)
from PyQt6.QtGui import QPixmap, QImage, QKeyEvent, qAlpha, QBrush, QColor
from PyQt6.QtCore import Qt, QRect, QTimer
import sys

def crop_transparent_edges(pixmap: QPixmap) -> QPixmap:
    """Обрезает прозрачные края у картинки"""
    image = pixmap.toImage().convertToFormat(QImage.Format.Format_ARGB32)

    left, top = image.width(), image.height()
    right, bottom = 0, 0

    for y in range(image.height()):
        for x in range(image.width()):
            if qAlpha(image.pixel(x, y)) > 0:
                left = min(left, x)
                right = max(right, x)
                top = min(top, y)
                bottom = max(bottom, y)

    if left > right or top > bottom:
        return QPixmap()  # Пустая картинка

    rect = QRect(left, top, right - left + 1, bottom - top + 1)
    return pixmap.copy(rect)

class DraggablePixmapItem(QGraphicsPixmapItem):
    def __init__(self, pixmap, scene, parent_app):
        super().__init__(pixmap)
        self.app_ref = parent_app
        self.scene_ref = scene
        self.setShapeMode(QGraphicsPixmapItem.ShapeMode.MaskShape)

        #self.default_color = QColor(0, 255, 0, 100)
        self.hover_color = QColor(0, 200, 255, 150)
        self.click_color = QColor(255, 0, 0, 150)
        #self.setBrush(QBrush(self.default_color))
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

    # def mousePressEvent(self, event):
    #     print(f"Клик по картинке + {self.item_id}")
    #     super().mousePressEvent(event)


    def mouseMoveEvent(self, event):
        if not self.fixed:
            super().mouseMoveEvent(event)

    def hoverEnterEvent(self, event):
        if not self.is_editable:
            effect = QGraphicsColorizeEffect()
            effect.setColor(QColor("green"))
            self.setGraphicsEffect(effect)


    def hoverLeaveEvent(self, event):
        if not self.is_editable:
            effect = QGraphicsColorizeEffect()
            effect.setColor(QColor("black"))
            self.setGraphicsEffect(effect)


    def mousePressEvent(self, event):
        print(f"Клик по картинке + {self.item_id}")
        super().mousePressEvent(event)
        # if not self.is_editable:
        #     effect = QGraphicsColorizeEffect()
        #     effect.setColor(QColor("blue"))
        #     self.setGraphicsEffect(effect)
        #     QTimer.singleShot(200, lambda: effect.setColor(QColor("black")))

        if event.button() == Qt.MouseButton.RightButton:
            menu = QMenu()
            delete_action = menu.addAction("Удалить")
            action2 = menu.addAction("Опция 2")
            # Используем screenPos, чтобы меню открылось в нужном месте
            selected_action = menu.exec(event.screenPos())
            if selected_action == delete_action:
                print("Выбрана Опция 1")
                self.scene_ref.removeItem(self)
                self.app_ref.remove_item(self)
            elif selected_action == action2:
                print("Выбрана Опция 2")
        else:
            super().mousePressEvent(event)


    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            self.old_pos = self.pos()  # Обновляем старую позицию при движении
        return super().itemChange(change, value)

    def freeze(self):
        """Зафиксировать картинку, блокируя её перемещение"""
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, False)
        self.fixed = True

    def check_overlap(self):
        """Проверка на перекрытие с другими картинками в сцене"""
        for item in self.scene_ref.items():
            if item is not self and isinstance(item, QGraphicsPixmapItem):
                if self.collidesWithItem(item):
                    return True
        return False

    def reset_position(self):
        """Возврат картинки в исходную позицию"""
        self.setPos(self.old_pos)

class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Добавление и закрепление картинок (обрезка фона)")
        self.resize(800, 640)

        self.view = QGraphicsView()
        self.scene = QGraphicsScene(self)
        self.view.setScene(self.scene)
        self.view.setSceneRect(0, 0, 800, 600)

        self.button = QPushButton("Add Picture")
        self.button.clicked.connect(self.add_next_item)

        layout = QVBoxLayout()
        layout.addWidget(self.view)
        layout.addWidget(self.button)
        self.setLayout(layout)

        # Фоновая картинка (без столкновений)
        background = QPixmap("drawing.png")
        background_item = QGraphicsPixmapItem(background)
        background_item.setZValue(-1)  # Отправляем фон на самый задний план
        self.scene.addItem(background_item)

        self.items = []
        self.current_item = None

    def remove_item(self, item):
        #self.app_ref.items.remove(self)
        if item in self.items:
            #self.scene.removeItem(item)
            self.items.remove(item)
            print(f"Удалено. Осталось {len(self.items)} элементов.")

    def add_next_item(self):
        if self.current_item is not None:
            print("Сначала закрепите текущую картинку (Enter).")
            return

        # Загружаем и обрезаем прозрачные края
        pixmap = QPixmap("circle.png")
        cropped = crop_transparent_edges(pixmap)

        item = DraggablePixmapItem(cropped, self.scene, self)
        item.setPos(50, 50)  # Начальная позиция
        item.old_pos = item.pos()  # Сохраняем её как исходную (начальную) позицию
        self.scene.addItem(item)
        self.current_item = item
        self.items.append(item)
        print(self.items)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.current_item:
                self.current_item.freeze()
                self.current_item.is_editable = False
                self.current_item = None
                # if self.current_item.check_overlap():
                #     print("Перекрытие! Картинка возвращена на исходную позицию.")
                #     # Возвращаем картинку на исходную позицию
                #     self.current_item.reset_position()
                # else:
                #     self.current_item.freeze()
                #     print("Картинка закреплена.")
                # self.current_item = None
        else:
            super().keyPressEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MyWidget()
    window.show()
    sys.exit(app.exec())
