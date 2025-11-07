from PyQt6.QtWidgets import (
    QWidget, QLabel, QTextEdit, QPushButton, QVBoxLayout, QLineEdit, QApplication,
    QMessageBox, QDialog, QFileDialog, QHBoxLayout, QScrollArea, QSizePolicy
)
from PyQt6.QtGui import QIcon, QPixmap, QGuiApplication
from PyQt6.QtCore import Qt
import sys
import image as im
import image_container
from track_object_state import ObjectState
import utils


class AddThing(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить вещь в пространство")
        self.setWindowIcon(QIcon(utils.resource_path("icons/mini_logo.png")))
        self.selected_file = ""

        screen_size = QGuiApplication.primaryScreen().size()
        screen_width = screen_size.width()
        screen_height = screen_size.height()
        width_coef = 0.4  # coefizient for width of Add Comment window
        height_coef = 0.6   #coefizient for height of Add Comment window
        self.setFixedSize(int(screen_width * width_coef), int(screen_height * height_coef))

        self.thing_images = []  # список для хранения загруженных SpaceImage

        # Виджеты для ввода названия и описания
        self.name_edit = QLineEdit()
        self.description_edit = QTextEdit()

        # Кнопки
        self.load_button = QPushButton("Загрузить фотографию вещи")
        self.ok_button = QPushButton("OK")
        self.cancel_button = QPushButton("Отмена")

        # Layout для изображений
        self.layout_images = QHBoxLayout()
        self.container_images = QWidget()
        self.container_images.setLayout(self.layout_images)
        self.container_images.adjustSize()

        # ScrollArea для изображений (горизонтальная прокрутка)
        self.scroll_for_images = QScrollArea()
        self.scroll_for_images.setWidgetResizable(True)
        self.scroll_for_images.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        self.scroll_for_images.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_for_images.setWidget(self.container_images)

        # Основной layout диалога
        main_layout = QVBoxLayout()
        main_layout.addWidget(QLabel("*Название вещи:"))
        main_layout.addWidget(self.name_edit)
        main_layout.addWidget(QLabel("Описание вещи:"))
        main_layout.addWidget(self.description_edit)
        main_layout.addWidget(self.scroll_for_images)
        main_layout.addWidget(self.load_button)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

        # Подключение сигналов
        self.load_button.clicked.connect(self.load_image)
        self.ok_button.clicked.connect(self.check_required_fields)
        self.cancel_button.clicked.connect(self.reject)

    def load_image(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выбрать изображение", "", "Images (*.png *.jpg *.bmp)"
        )
        if file_path:
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                QMessageBox.warning(self, "Ошибка", "Не удалось загрузить изображение.")
                return

            thing_image = im.SpaceImage(pixmap)
            thing_image.mark_new()
            self.thing_images.append(thing_image)
            self.update_images_layout()

    def clear_layout(self, layout=None):
        if layout is None:
            layout = self.layout_images
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())

    def update_images_layout(self):
        self.clear_layout()
        for item in self.thing_images:
            image_widget = image_container.ImageContainer(item, self.container_images.contentsRect().height())
            image_widget.delete_image.connect(self.delete_image)
            image_widget.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
            if not image_widget.space_image.state == ObjectState.DELETED:
                self.layout_images.addWidget(image_widget)
        self.layout_images.addStretch()  # Чтобы изображения прижались к левому краю

    def delete_image(self, image):
        if image in self.thing_images:
            if image.state == ObjectState.NEW:
                self.thing_images.remove(image)
            else:
                image.mark_deleted()


    def check_required_fields(self):
        if not self.name_edit.text():
            QMessageBox.warning(self, "Заполните обязательные поля",
                                "Пожалуйста укажите название вещи!")
        else:
            self.accept()


    def get_data(self):
        # Возвращаем имя, описание, картинку
        return {
            "name": self.name_edit.text(),
            "description": self.description_edit.toPlainText() if self.description_edit.toPlainText() else None,
            "thing_images": self.thing_images if self.thing_images else None
        }