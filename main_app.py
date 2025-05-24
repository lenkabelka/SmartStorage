from PyQt6.QtWidgets import (
    QApplication, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem,
    QGraphicsItem, QVBoxLayout, QPushButton, QWidget, QGraphicsColorizeEffect,
    QMenu, QGridLayout, QHBoxLayout, QLabel, QScrollArea, QSizePolicy, QMessageBox, QStackedLayout, QFrame,
    QStackedWidget, QFileDialog, QTreeView, QMenuBar, QMainWindow
)
from PyQt6.QtGui import QPixmap, QImage, QKeyEvent, qAlpha, QBrush, QColor, QMouseEvent, QPainter, QFont, \
    QStandardItemModel, QStandardItem, QPainterPath, QAction
from PyQt6.QtCore import Qt, QRect, QPointF, pyqtSignal, QRectF
import sys
import add_projection as add_projection
import add_space as add_space
import draggable_pixmap_item as draggable_item
import image_utils as utils
import queries_for_DB as query
import image_container
import space
import zoomable_graphics_view
from typing import Optional, List
import projection as pr

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Smart Storage")

        action_exit = QAction("Exit", self)
        action_exit.triggered.connect(self.close)
        menu = self.menuBar()
        file_menu = menu.addMenu("&File")
        about_menu = menu.addMenu("&About")
        file_menu.addAction(action_exit)

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

        self.setCentralWidget(MainWidget())


class MainWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.space_name = ""
        self.background = None
        self.background_item = None
        self.parent_space = space.Space("", "")
        self.parent_space.space_images = None
        #self.images_of_space = []
        self.parent_space.current_projection = None
        self.subprojections = []

        self.x_scale = None
        self.y_scale = None

        self.stack_widget = QStackedWidget()

        #self.items = []
        self.current_subspace = None

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
        self.container_projections_of_space = QWidget()  # контейнер для развертки

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


        self.scene = QGraphicsScene(self)
        self.view = zoomable_graphics_view.ZoomableGraphicsView(self.scene)
        self.scene.addItem(self.placeholder_for_projection)
        self.view.setScene(self.scene)
        #self.view.setSceneRect(0, 0, 800, 600)

        self.button_layout = QVBoxLayout()

        self.add_projection_of_space_button = QPushButton("Add projection of space")
        ##############self.add_projection_of_space_button.clicked.connect(self.add_projection_of_space)
        self.add_projection_of_space_button.clicked.connect(self.add_space_projection)

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

        if self.parent_space.subspaces:
            for subspace in self.parent_space.subspaces:
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


    def add_space_projection(self):
        add_projection_dialog = add_projection.AddProjection()
        while True:
            if add_projection_dialog.exec():
                temp_dict_new_space_projection = add_projection_dialog.get_data()

                if not temp_dict_new_space_projection["name"]:
                    QMessageBox.warning(self, "Заполните обязательные поля",
                                        "Пожалуйста укажите название проекции!")
                elif not temp_dict_new_space_projection["image"]:
                    QMessageBox.warning(self, "Заполните обязательные поля",
                                        "Пожалуйста загрузите изображение проекции!")

                else:
                    projection_name = temp_dict_new_space_projection["name"]
                    print("Punkt_1")


                    is_name_busy = False
                    if self.parent_space.projections:
                        is_name_busy = any(p.projection_name == projection_name for p in self.parent_space.projections)


                    #if projection_name != self.parent_space.current_projection.projection_name:

                    if not is_name_busy:
                        print("Punkt_3")

                        # class Projection:
                        #     projection_name: str
                        #     projection_image: QPixmap
                        #     x_scale: float
                        #     y_scale: float
                        #     reference_to_parent_space: Optional["space.Space"]
                        #     scaled_projection_image: draggable_pixmap_item.DraggablePixmapItem | QGraphicsPixmapItem | None = None
                        #     reference_to_parent_projection: Optional["Projection"] | None = None
                        #     projection_description: str | None = None
                        #     x_pos: float | None = None
                        #     y_pos: float | None = None

                        # Добавление новой картинки
                        if self.parent_space.current_projection is None:

                            original_image = temp_dict_new_space_projection["image"]
                            print("Punkt_4")
                            scaled_image = utils.calculate_new_image_size(original_image,
                                                                          temp_dict_new_space_projection["x_sm"],
                                                                          temp_dict_new_space_projection["y_sm"])


                            print("Punkt_4")

                            scaled_cropped_pixmap = utils.get_scaled_pixmap_1(
                                original_image,
                                scaled_image.width(),
                                scaled_image.height()
                            )

                            self.x_scale = scaled_cropped_pixmap.width() / temp_dict_new_space_projection["x_sm"]
                            self.y_scale = scaled_cropped_pixmap.height() / temp_dict_new_space_projection["y_sm"]

                            print(f"scaled_cropped_pixmap.width: {scaled_cropped_pixmap.width()}")
                            print(f"scaled_cropped_pixmap.height: {scaled_cropped_pixmap.height()}")
                            projection = pr.Projection(temp_dict_new_space_projection["name"],
                                                       original_image,
                                                       temp_dict_new_space_projection["x_sm"],
                                                       temp_dict_new_space_projection["y_sm"],
                                                       self.parent_space,
                                                       scaled_cropped_pixmap)

                            if temp_dict_new_space_projection["description"]:
                                projection.projection_description = temp_dict_new_space_projection["description"]

                            if self.parent_space.projections is None:
                                self.parent_space.projections = []
                            self.parent_space.projections.append(projection)

                            self.parent_space.current_projection = projection

                            self.background = QPixmap(scaled_cropped_pixmap)
                            print(f"фон: {self.background}")
                            self.background_item = QGraphicsPixmapItem(self.background)

                            min_z = min((item.zValue() for item in self.scene.items()), default=0)
                            print(f"min_z: {min_z}")

                            self.background_item.setZValue(min_z - 1)  # Отправляем фон на самый задний план
                            print(f"background_z: {self.background_item.zValue()}")
                            self.background_item.setPos(0, 0)
                            self.scene.removeItem(self.placeholder_for_projection)
                            self.scene.addItem(self.background_item)

                            #self.view.setAlignment(Qt.AlignmentFlag.AlignCenter)
                            self.view.fitInView(self.background_item, Qt.AspectRatioMode.KeepAspectRatio)

                            #TODO при загрузке бублика появляются scrollbar и размер view слишком большой
                            print(f"view_w: {self.view.width()}")
                            print(f"view_h: {self.view.height()}")

                            self.add_projection_of_space_button.setText("Change space projection")

                            break

                        # Замена существующей фоновой картинки и других данных о развертке
                        else:
                            print("PUNKT_ELSE!")
                            if self.background_item:
                                self.scene.removeItem(self.background_item)

                            #self.parent_space.current_projection = None
                            temp_dict_new_space_projection = add_projection_dialog.get_data()

                            #original_image = utils.crop_transparent_edges(QPixmap.fromImage(temp_dict_new_space_projection["image"]))
                            original_image = temp_dict_new_space_projection["image"]
                            scaled_image = utils.calculate_new_image_size(original_image,
                                                                          temp_dict_new_space_projection["x_sm"],
                                                                          temp_dict_new_space_projection["y_sm"])

                            scaled_cropped_pixmap = utils.get_scaled_pixmap_1(
                                original_image,
                                scaled_image.width(),
                                scaled_image.height()
                            )

                            self.x_scale = scaled_cropped_pixmap.width() / temp_dict_new_space_projection["x_sm"]
                            self.y_scale = scaled_cropped_pixmap.height() / temp_dict_new_space_projection["y_sm"]

                            print(f"original_image.width: {original_image.width()}")
                            print(f"original_image.height: {original_image.height()}")

                            self.parent_space.current_projection.projection_image = original_image
                            self.parent_space.current_projection.x_sm = temp_dict_new_space_projection["x_sm"]
                            self.parent_space.current_projection.y_sm = temp_dict_new_space_projection["y_sm"]

                            self.parent_space.current_projection.projection_name = temp_dict_new_space_projection["name"]
                            if temp_dict_new_space_projection["description"]:
                                self.parent_space.current_projection.projection_description \
                                    = temp_dict_new_space_projection["description"]
                            print(f"старый_фон: {self.background}")
                            self.background = QPixmap(scaled_cropped_pixmap)
                            print(f"новый_фон: {self.background}")
                            self.background_item = QGraphicsPixmapItem(self.background)

                            min_z = min((item.zValue() for item in self.scene.items()), default=0)

                            self.background_item.setZValue(min_z - 1)  # Отправляем фон на самый задний план
                            self.background_item.setPos(0, 0)
                            #self.scene.removeItem(self.placeholder_for_projection)
                            self.scene.addItem(self.background_item)
                            self.view.fitInView(self.background_item, Qt.AspectRatioMode.KeepAspectRatio)
                            # Масштабирование сцены под размер виджета
                            # self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
                            # self.view.setResizeAnchor(QGraphicsView.ViewportAnchor.AnchorViewCenter)
                            # self.view.fitInView(self.background_item, Qt.AspectRatioMode.KeepAspectRatio)

                            if self.parent_space.sub_projections:

                                for subproj in self.parent_space.sub_projections:
                                    if subproj.reference_to_parent_projection == self.parent_space.current_projection:
                                        print(f"subproj: {subproj}")
                                        subproj.scaled_projection_pixmap.update_path(self.background)

                            break

                    else:
                        QMessageBox.warning(self, "Имя занято", "Такое имя уже существует. Пожалуйста, введите другое.")
                        # не очищаем — пользователь увидит свои прежние данные

                        break
            else:
                break  # пользователь нажал "Отмена" — выходим



    def add_subspace(self):
        # if self.current_item is not None:
        #     print("Сначала закрепите текущую картинку (Enter).")
        #     return

        add_subspace_dialog = add_space.AddSpace()

        while True:
            if add_subspace_dialog.exec():
                dict_of_new_space = add_subspace_dialog.get_data()

                if not dict_of_new_space["name"]:
                    QMessageBox.warning(self, "Заполните обязательные поля",
                                        "Пожалуйста укажите название пространства!")
                else:
                    name = dict_of_new_space["name"]

                    is_name_busy = False
                    if self.parent_space.subspaces:
                        is_name_busy = next((subspace for subspace in self.parent_space.subspaces if subspace.name == name), None)

                    if is_name_busy or name == self.parent_space.name:
                        QMessageBox.warning(self, "Имя занято", "Такое имя уже существует. Пожалуйста, введите другое.")

                    else:

                        new_space = space.Space(name, dict_of_new_space["description"])


                        #print(self.parent_space)

                        if self.parent_space.subspaces is None:
                            self.parent_space.subspaces = []
                        self.parent_space.subspaces.append(new_space)
                        #self.subspaces.append(new_space)

                        self.current_index = 1
                        self.stack_widget.setCurrentIndex(self.current_index)

                        #self.add_projection_of_subspace(new_space)
                        self.add_subspace_projection(new_space)
                        self.update_tree_view()

                    break  # успех — выходим из цикла
            else:
                break  # пользователь нажал "Отмена" — выходим



    def add_subspace_projection(self, subspace: space.Space):
        if not self.parent_space.current_projection:
            QMessageBox.warning(self, "Добавьте проекцию пространства",
                                "Если хотите также добавить проекцию подпространства, то "
                                "необходимо вначале добавить проекцию пространства!")
            return

        add_projection_of_subspace_dialog = add_projection.AddProjection()

        while True:
            if add_projection_of_subspace_dialog.exec():
                temp_dict_new_subspace_projection = add_projection_of_subspace_dialog.get_data()

                if not temp_dict_new_subspace_projection["name"]:
                    QMessageBox.warning(self, "Заполните обязательные поля",
                                        "Пожалуйста укажите название проекции!")
                elif not temp_dict_new_subspace_projection["image"]:
                    QMessageBox.warning(self, "Заполните обязательные поля",
                                        "Пожалуйста загрузите изображение проекции!")
                else:

                    projection_name = temp_dict_new_subspace_projection["name"]

                    print(f"x_sm: {temp_dict_new_subspace_projection["x_sm"]}")
                    print(f"y_sm: {temp_dict_new_subspace_projection["y_sm"]}")


                    is_projection_name_busy = False
                    if self.parent_space.sub_projections:
                        is_projection_name_busy = next((name for name in self.parent_space.sub_projections
                                                        if name.projection_name == projection_name), None)


                    if not is_projection_name_busy:
                        original_image = temp_dict_new_subspace_projection["image"]
                        print(f"original_image_sub.width: {original_image.width()}")
                        print(f"original_image_sub.height: {original_image.height()}")

                        pixmap = utils.get_scaled_pixmap_1(
                            temp_dict_new_subspace_projection["image"],
                            int(round(self.x_scale * temp_dict_new_subspace_projection["x_sm"])),
                            int(round(self.y_scale * temp_dict_new_subspace_projection["y_sm"]))
                        )

                            # class Projection:
                            #     projection_name: str
                            #     projection_image: QImage
                            #     x_sm: float
                            #     y_sm: float
                            #     reference_to_parent_space: Optional["space.Space"]
                            #     scaled_projection_pixmap: draggable_pixmap_item.DraggablePixmapItem | QPixmap | None = None
                            #     reference_to_parent_projection: Optional["Projection"] | None = None
                            #     projection_description: str | None = None
                            #     x_pos: float | None = None
                            #     y_pos: float | None = None


                        sub_projection = pr.Projection(temp_dict_new_subspace_projection["name"],
                                                       original_image,
                                                       temp_dict_new_subspace_projection["x_sm"],
                                                       temp_dict_new_subspace_projection["y_sm"],
                                                       subspace)
                        print("I am here!")
                        if self.parent_space.sub_projections is None:
                            print(type(self.parent_space.sub_projections))
                            self.parent_space.sub_projections = []
                            print(self.parent_space.sub_projections)
                        #self.parent_space.sub_projections.append(sub_projection)
                        print(type(self.parent_space.sub_projections))

                        # родитель подразвертки это развертка, которая на данный момент отображается как background
                        sub_projection.reference_to_parent_projection = self.parent_space.current_projection

                        item = draggable_item.DraggablePixmapItem(pixmap, self.scene, self, self.background)

                        #sub_projection.scaled_projection_image = item
                        sub_projection.scaled_projection_pixmap = item

                        if temp_dict_new_subspace_projection["description"]:
                            sub_projection.projection_description = temp_dict_new_subspace_projection["description"]

                        self.parent_space.sub_projections.append(sub_projection)

                        item.setPos(0, 0)
                        item.old_pos = item.pos()
                        self.scene.addItem(item)
                        self.current_subspace = item


                        print(f"background: {self.background}")
                        print(f"background_item: {self.background_item}")

                        #print(f"item_width: {item.width()}")
                        #print(f"item_height: {item.height()}")


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
            if not self.parent_space.space_images:
                self.parent_space.space_images = []
            # Сохраняем само изображение (QPixmap) в переменную
            self.parent_space.space_images.append(QPixmap(file_path))

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

            for pixmap in self.parent_space.space_images:
                image_widget = image_container.ImageContainer(pixmap, self.container_images_of_space.contentsRect().height())
                image_widget.delete_image.connect(self.delete_image_from_list)

                self.layout_images_of_space.addWidget(image_widget)
                self.layout_images_of_space.setAlignment(Qt.AlignmentFlag.AlignLeft)


    def delete_image_from_list(self, pointer):
        print(f"До удаления: {self.parent_space.space_images}")

        if pointer in self.parent_space.space_images:
            self.parent_space.space_images.remove(pointer)
            print(f"После удаления: {self.parent_space.space_images}")


    def save_space_to_DB(self):

        print("save")
        id_parent_space = query.insert_space(self.parent_space.name, self.parent_space.description)
        print(id_parent_space)
        print(self.parent_space.projections)

        for projection in self.parent_space.projections:


            id_parent_projection = query.insert_projection_of_space(id_parent_space,
                                                                    projection.projection_name,
                                                                    projection.projection_description,
                                                                    QPixmap(projection.projection_image),
                                                                    projection.projection_width,
                                                                    projection.projection_height)
            print("ЦИКЛ")

            for sub_projection in self.parent_space.sub_projections:
                if sub_projection.reference_to_parent_projection == projection:
                    sub_projection.id_parent_projection = id_parent_projection

        for subspace in self.parent_space.subspaces:
            id_parent_subspace = query.insert_subspace(id_parent_space, subspace.name, subspace.description)

            for sub_projection in self.parent_space.sub_projections:
                if sub_projection.reference_to_parent_space == subspace:
                    sub_projection.id_parent_space = id_parent_subspace


        for sub_projection in self.parent_space.sub_projections:
            pixmap_item = sub_projection.scaled_projection_pixmap
            background_item = self.background_item

            if pixmap_item and background_item:
                if pixmap_item.scene() and background_item.scene():
                    scene_pos = pixmap_item.mapToScene(0, 0)
                    relative_pos = background_item.mapFromScene(scene_pos)
                    print(f"Relative position: {relative_pos}")
                else:
                    print("Один из элементов не добавлен в сцену")
            else:
                print("Один из элементов не инициализирован")

            print("scaled_projection_pixmap:", sub_projection.scaled_projection_pixmap)
            print("background_item:", self.background_item)

            relative_pos = self.background_item.mapFromItem(sub_projection.scaled_projection_pixmap, 0, 0)
            query.insert_projection_of_subspace(sub_projection.id_parent_projection,
              sub_projection.id_parent_space,
              sub_projection.projection_name,
              sub_projection.projection_description,
              relative_pos.x(),
              relative_pos.y(),
              QPixmap(sub_projection.projection_image),
              sub_projection.projection_width,
              sub_projection.projection_height)







        # id_parent_projection = query.insert_projection_of_space(id_parent_space, self.parent_space.projection_name,
        #                                                  self.parent_space.projection_description,
        #                                                  self.parent_space.projection_image)
        # print(id_parent_projection)
        #
        # if self.subspaces:
        #     for subspace in self.subspaces:
        #         print(subspace.name)
        #         print(subspace.description)
        #         id_parent_subspace = query.insert_subspace(id_parent_space, subspace.name, subspace.description)

                # id_projection
                # id_parent_projection
                # id_parent_space (id_parent_subspace)
                # projection_name
                # projection_description
                # x_pos_in_parent_projection
                # y_pos_in_parent_projection
                # projection_image

                # query.insert_projection_of_subspace(id_parent_projection,
                #                                     id_parent_subspace,
                #                                     subspace.projection_name,
                #                                     subspace.projection_description,
                #                                     subspace.x_pos,
                #                                     subspace.y_pos,
                #                                     subspace.projection_image)

        # if self.images_of_space:
        #     for item in self.images_of_space:
        #         query.insert_image(utils.pixmap_to_bytes(item), parent_id)
        # print("saved")

        # При удалении подпространства необходимо удалить
        # его подразвертку из self.sub_projections
        # и его пространство из self.subspaces и также саму картинку со сцены
    def remove_subspace(self, draggable_item_pointer):
        # Находим объект Projection, который содержит картинку , по которой был произведен щелчок:
        print("Punkt_1")
        subprojection_to_remove = next((projection for projection in self.parent_space.sub_projections
                                    if projection.scaled_projection_image == draggable_item_pointer), None)
        print(subprojection_to_remove)
        print("Punkt_2")
        subspace_to_remove = next((subspace for subspace in self.parent_space.subspaces
                                   if subspace == subprojection_to_remove.reference_to_parent_space), None)
        print(subspace_to_remove)
        print("Punkt_3")
        print(f"subspaces до удаления: {self.parent_space.subspaces.remove}")
        self.parent_space.subspaces.remove(subspace_to_remove)
        print(f"subspaces после удаления: {self.parent_space.subspaces.remove}")

        print(f"sub_projections до удаления: {self.parent_space.sub_projections}")
        self.parent_space.sub_projections.remove(subprojection_to_remove)
        print(f"sub_projections после удаления: {self.parent_space.sub_projections}")


    def unfreeze_subspace(self, item):
        self.current_subspace = item
        self.current_subspace.unfreeze()
        self.current_subspace.is_editable = True



if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())