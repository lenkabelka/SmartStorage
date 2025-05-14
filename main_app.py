from PyQt6.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QGraphicsItem, QVBoxLayout, QPushButton, QWidget, QGraphicsColorizeEffect,
    QMenu, QGridLayout, QHBoxLayout, QLabel, QScrollArea, QSizePolicy, QMessageBox, QStackedLayout, QFrame,
    QStackedWidget, QFileDialog, QTreeView
)
from PyQt6.QtGui import QPixmap, QImage, QKeyEvent, qAlpha, QBrush, QColor, QMouseEvent, QPainter, QFont, QStandardItemModel, QStandardItem, QPainterPath
from PyQt6.QtCore import Qt, QRect, QPointF, pyqtSignal, QRectF
import sys
import add_projection as add_projection
import add_space as add_space
import draggable_pixmap_item as draggable_item
import image_utils as utils
import queries_for_DB as query
import image_container
import space



class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Smart Storage")
        self.space_name = ""
        self.background = None
        self.background_item = None

        screen = QApplication.primaryScreen().geometry()
        coef_width = 0.9
        coef_height = 0.9
        window_width = int(screen.width() * coef_width)
        window_height = int(screen.height() * coef_height)
        self.resize(window_width, window_height)
        x = (screen.width() - window_width) // 2
        y = 0
        #y = (screen.height() - window_height) // 2
        self.move(x, y)

        self.parent_space = space.Space("", "")
        self.subspaces = []
        self.images_of_space = []

        self.stack_widget = QStackedWidget()

        self.items = []
        self.current_item = None

############## wellcome page ###########################################################################################

        self.wellcome_page = QFrame()
        #self.wellcome_page.resize(window_width, window_height)
        self.wellcome_layout = QVBoxLayout()

        self.wellcome_label = QLabel("Добро пожаловать в программу умного хранения вещей!")
        self.add_space_button = QPushButton("Add new space")
        self.open_saved_space_button = QPushButton("Open saved space")

        self.wellcome_layout.addWidget(self.wellcome_label)
        self.wellcome_layout.addWidget(self.add_space_button)
        self.wellcome_layout.addWidget(self.open_saved_space_button)

        self.wellcome_page.setLayout(self.wellcome_layout)

############## opened space page ###########################################################################################

        self.create_or_change_space = QFrame()

        self.layout_main = QGridLayout()

        self.left_layout = QVBoxLayout()
        self.right_layout = QGridLayout()#QHBoxLayout()

        self.layout_space_creation = QVBoxLayout()
        self.container_images_of_space = QWidget()
        #container_images_of_space.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Maximum)
        self.layout_images_of_space = QHBoxLayout()

        self.scroll_for_images = QScrollArea()
        self.scroll_for_images.setWidgetResizable(True)
        self.scroll_for_images.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        #scroll_for_images.setWidgetResizable(True)
        #scroll_for_images.adjustSize()
        #scroll_for_images.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

        self.layout_projections_of_space = QVBoxLayout()
        self.container_projections_of_space = QWidget()
        self.scroll_for_projections_of_space = QScrollArea()
        self.scroll_for_projections_of_space.setWidgetResizable(True)
        self.scroll_for_projections_of_space.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.container_projections_of_space.setLayout(self.layout_projections_of_space)
        self.container_projections_of_space.adjustSize()
        self.scroll_for_projections_of_space.setWidget(self.container_projections_of_space)


        self.container_images_of_space.setLayout(self.layout_images_of_space)
        self.container_images_of_space.adjustSize()
        self.scroll_for_images.setWidget(self.container_images_of_space)
        #layout_images_of_space.setContentsMargins(0, 0, 0, 0)
        #scroll_for_images.setContentsMargins(0, 0, 0, 0)
        #scroll_for_images.adjustSize()


        #layout_images_of_space.addWidget(scroll_for_images)

        self.pixmap_placeholder = QPixmap(300, 300)

        painter = QPainter(self.pixmap_placeholder)
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Arial", 20))
        painter.drawText(self.pixmap_placeholder.rect(), Qt.AlignmentFlag.AlignCenter, "Hello!")
        painter.end()

        self.placeholder_for_projection = QGraphicsPixmapItem(self.pixmap_placeholder)

        self.view = QGraphicsView()
        self.scene = QGraphicsScene(self)
        self.scene.addItem(self.placeholder_for_projection)
        self.view.setScene(self.scene)
        self.view.setSceneRect(0, 0, 800, 600)

        self.button_layout = QVBoxLayout()

        self.add_projection_of_space_button = QPushButton("Add projection of space")
        self.add_projection_of_space_button.clicked.connect(self.add_projection_of_space)

        self.add_subspace_button = QPushButton("Add subspace")
        self.add_subspace_button.clicked.connect(self.add_subspace)

        #self.add_projection_of_subspace_button = QPushButton("Add projection of subspace")
        #self.add_projection_of_subspace_button.clicked.connect(self.add_projection_of_subspace)

        self.add_image_of_space_button = QPushButton("Add image of space")
        self.add_image_of_space_button.clicked.connect(self.add_image_of_space)

        self.save_space_button = QPushButton("Save space")
        self.save_space_button.clicked.connect(self.save_space_to_DB)

        self.button_layout.addWidget(self.add_projection_of_space_button)
        self.button_layout.addWidget(self.add_subspace_button)
        self.button_layout.addWidget(self.add_image_of_space_button)
        self.button_layout.addWidget(self.save_space_button)

        self.layout_space_creation.addWidget(self.view)
        #self.layout_space_creation.addWidget(self.add_projection_of_space_button)
        #self.layout_space_creation.addWidget(self.add_subspace_button)
        #self.layout_space_creation.addWidget(self.add_projection_of_subspace_button)
        #self.layout_space_creation.addWidget(self.save_space_button)
        #self.layout_space_creation.addWidget(self.add_image_of_space_button)

        self.layout_main.addLayout(self.layout_space_creation, 0, 0)#, 3, 2)
        self.layout_main.setRowStretch(0, 4)

        self.layout_main.addLayout(self.button_layout, 1, 0)
        self.layout_main.setRowStretch(1, 1)
        self.layout_main.addWidget(self.scroll_for_images, 2, 0)#, 1, 2)
        self.layout_main.setRowStretch(2, 2)

        #self.left_view_frame = QFrame()
        #self.left_view_layout

        self.tree = QTreeView()
        #self.model = QStandardItemModel()
        #model.setHorizontalHeaderLabels(["Название", "Описание"])
        #self.tree.setModel(self.model)
        #self.tree.expandAll()


        #self.left_layout = QHBoxLayout()
        self.right_layout.addWidget(self.scroll_for_projections_of_space, 0, 0)
        self.layout_main.setColumnStretch(0, 1)
        self.right_layout.addWidget(self.tree, 0, 1)
        self.layout_main.setColumnStretch(1, 1)


        self.layout_main.addLayout(self.right_layout, 0, 1, 3, 1)
        self.layout_main.setColumnStretch(0, 2)
        self.layout_main.setColumnStretch(1, 1)

        self.create_or_change_space.setLayout(self.layout_main)


        self.stack_widget.addWidget(self.wellcome_page)
        self.stack_widget.addWidget(self.create_or_change_space)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.stack_widget)
        self.setLayout(main_layout)

        self.current_index = 0

############## connections #############################################################################################
        self.add_space_button.clicked.connect(self.add_space)


    def update_tree_view(self):
        model = QStandardItemModel()

        root_space = QStandardItem(self.parent_space.name)
        root_space.setEditable(False)

        for subspace in self.subspaces:
            sub_space = QStandardItem(subspace.name)
            sub_space.setEditable(False)
            root_space.appendRow(sub_space)

        model.appendRow(root_space)
        self.tree.setModel(model)
        self.tree.expandAll()


    def add_space(self):
        add_space_dialog = add_space.AddSpace()

        while True:
            if add_space_dialog.exec():
                dict_of_new_space = add_space_dialog.get_data()

                if not dict_of_new_space["name"]:
                    QMessageBox.warning(self, "Заполните обязательные поля",
                                        "Пожалуйста укажите название пространства!")
                else:

                    name = dict_of_new_space["name"]

                    if name != self.parent_space.name:
                        self.parent_space = space.Space(name, dict_of_new_space["description"])

                        self.current_index = 1
                        self.stack_widget.setCurrentIndex(self.current_index)

                        self.update_tree_view()

                        break  # успех — выходим из цикла
                    else:
                        QMessageBox.warning(self, "Имя занято", "Такое имя уже существует. Пожалуйста, введите другое.")
                        # не очищаем — пользователь увидит свои прежние данные
            else:
                break  # пользователь нажал "Отмена" — выходим


    def add_projection_of_space(self):
        add_space_dialog = add_projection.AddSpaceOrSubspace()
        while True:
            if add_space_dialog.exec():
                dict_of_new_space_projection = add_space_dialog.get_data()

                if not dict_of_new_space_projection["name"]:
                    QMessageBox.warning(self, "Заполните обязательные поля",
                                        "Пожалуйста укажите название проекции!")
                elif not dict_of_new_space_projection["image"]:
                        QMessageBox.warning(self, "Заполните обязательные поля",
                                            "Пожалуйста загрузите изображение проекции!")
                else:

                    projection_name = dict_of_new_space_projection["name"]

                    if projection_name != self.parent_space.projection_name:
                        pixmap = utils.get_scaled_pixmap(
                            dict_of_new_space_projection["image"],
                            dict_of_new_space_projection["x_scale"],
                            dict_of_new_space_projection["y_scale"]
                        )

                        self.parent_space.projection_name = projection_name
                        self.parent_space.projection_description = dict_of_new_space_projection["description"]

                        print(self.parent_space.projection_image)

                        # Фоновая картинка
                        self.background = QPixmap(pixmap)
                        self.background_item = QGraphicsPixmapItem(self.background)

                        self.background_item.setZValue(-1)  # Отправляем фон на самый задний план
                        self.scene.removeItem(self.placeholder_for_projection)
                        self.scene.addItem(self.background_item)

                        self.parent_space.projection_image = self.background_item

                        break  # успех — выходим из цикла
                    else:
                        QMessageBox.warning(self, "Имя занято", "Такое имя уже существует. Пожалуйста, введите другое.")
                        # не очищаем — пользователь увидит свои прежние данные
            else:
                break  # пользователь нажал "Отмена" — выходим


    def add_subspace(self):
        if self.current_item is not None:
            print("Сначала закрепите текущую картинку (Enter).")
            return

        add_subspace_dialog = add_space.AddSpace()

        while True:
            if add_subspace_dialog.exec():
                dict_of_new_space = add_subspace_dialog.get_data()

                if not dict_of_new_space["name"]:
                    QMessageBox.warning(self, "Заполните обязательные поля",
                                        "Пожалуйста укажите название пространства!")
                else:
                    name = dict_of_new_space["name"]

                    is_name_busy = next((subspace for subspace in self.subspaces if subspace.name == name), None)

                    if is_name_busy or name == self.parent_space.name:
                        QMessageBox.warning(self, "Имя занято",
                                            "Такое имя уже существует. Пожалуйста, введите другое.")

                    else:

                        new_space = space.Space(name, dict_of_new_space["description"])
                        self.subspaces.append(new_space)

                        self.current_index = 1
                        self.stack_widget.setCurrentIndex(self.current_index)

                        self.add_projection_of_subspace(new_space)

                        self.update_tree_view()

                        break  # успех — выходим из цикла
            else:
                break  # пользователь нажал "Отмена" — выходим


    def add_projection_of_subspace(self, subspace: space.Space):

        if not self.parent_space.projection_image:
            QMessageBox.warning(self, "Добавьте проекцию пространства",
                                "Чтобы добавить проекцию подпространства в пространство, "
                                "необходимо вначале добавить проекцию пространства!")
        else:
            add_projection_of_subspace_dialog = add_projection.AddSpaceOrSubspace()  # создаём диалог один раз

            while True:
                if add_projection_of_subspace_dialog.exec():

                    temp_dict_new_subspace_projection = add_projection_of_subspace_dialog.get_data()
                    projection_name = temp_dict_new_subspace_projection["name"]

                    is_projection_name_busy = next((subspace for subspace in self.subspaces
                                                    if subspace.projection_name == projection_name), None)

                    if not is_projection_name_busy:
                        pixmap = utils.get_scaled_pixmap(
                            temp_dict_new_subspace_projection["image"],
                            temp_dict_new_subspace_projection["x_scale"],
                            temp_dict_new_subspace_projection["y_scale"]
                        )

                        item = draggable_item.DraggablePixmapItem(pixmap, self.scene, self, self.background)
                        item.setPos(60, 60)
                        item.old_pos = item.pos()
                        self.scene.addItem(item)
                        self.current_item = item

                        print(self.current_item)

                        subspace.projection_name = projection_name
                        subspace.projection_description = temp_dict_new_subspace_projection["description"]
                        subspace.projection_image = item

                        print(item)

                        break  # успех — выходим из цикла
                    else:
                        QMessageBox.warning(self, "Имя занято", "Такое имя уже существует. Пожалуйста, введите другое.")
                        # не очищаем — пользователь увидит свои прежние данные
                else:
                    break  # пользователь нажал "Отмена" — выходим


    def add_image_of_space(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выбрать изображение", "", "Images (*.png *.jpg *.bmp)"
        )

        if file_path:
            # Сохраняем само изображение (QPixmap) в переменную
            self.images_of_space.append(QPixmap(file_path))

            def clear_layout(layout):
                for i in reversed(range(layout.count())):
                    item = layout.itemAt(i)
                    if item is not None:
                        widget = item.widget()
                        if widget:
                            widget.deleteLater()
                        else:
                            sublayout = item.layout()
                            clear_layout(sublayout)

            clear_layout(self.layout_images_of_space)

            for pixmap in self.images_of_space:
                image_widget = image_container.ImageContainer(pixmap, self.container_images_of_space.contentsRect().height())
                image_widget.delete_image.connect(self.delete_image_from_list)

                self.layout_images_of_space.addWidget(image_widget)
                self.layout_images_of_space.setAlignment(Qt.AlignmentFlag.AlignLeft)


    def delete_image_from_list(self, pointer):
        print(f"До удаления: {self.images_of_space}")

        if pointer in self.images_of_space:
            self.images_of_space.remove(pointer)
            print(f"После удаления: {self.images_of_space}")


    def save_space_to_DB(self):
        print("save")
        id_parent_space = query.insert_space(self.parent_space.name, self.parent_space.description)
        print(id_parent_space)
        id_projection = query.insert_projection_of_space(id_parent_space, self.parent_space.projection_name,
                                                         self.parent_space.projection_description, self.parent_space.projection_image)
        print(id_projection)

        if self.subspaces:
            for subspace in self.subspaces:
                print(subspace.name)
                print(subspace.description)
                query.insert_subspace(id_parent_space, subspace.name, subspace.description)

        # if self.images_of_space:
        #     for item in self.images_of_space:
        #         query.insert_image(utils.pixmap_to_bytes(item), parent_id)
        # print("saved")


    def remove_item(self, subspace_pointer):
        print("До удаления:")
        for sub in self.subspaces:
            print(sub)

        print(f"subspace_pointer: {subspace_pointer}")

        subspace_to_remove = next((subspace for subspace in self.subspaces if subspace.projection_image == subspace_pointer), None)
        print(subspace_to_remove)
        if subspace_to_remove:
            print("Удаляем!")
            self.subspaces.remove(subspace_to_remove)

        print("После удаления:")
        for i in self.subspaces:
            print(i)


    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self.current_item:

                subspace_to_change = next((item for item in self.subspaces if item.projection_image == self.current_item),
                                          None)
                print(subspace_to_change)

                if subspace_to_change:

                    print("Я в иф!")
                    print(f"родитель: {self.parent_space.projection_image}")

                    position_of_subspace_relative_space = self.current_item.mapToItem(self.parent_space.projection_image, QPointF(0, 0))

                    print("Я всё ещё в иф!")

                    subspace_to_change.x_pos = position_of_subspace_relative_space.x()
                    print(subspace_to_change.x_pos)
                    subspace_to_change.y_pos = position_of_subspace_relative_space.y()
                    print(subspace_to_change.y_pos)
                else:
                    print("Они не равны!")

                self.current_item.freeze()
                self.current_item.is_editable = False
                self.current_item = None
        else:
            super().keyPressEvent(event)


    def unfreeze_subspace(self, item):
        self.current_item = item
        self.current_item.unfreeze()
        self.current_item.is_editable = True



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())