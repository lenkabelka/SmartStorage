from PyQt6.QtWidgets import (
    QApplication, QGraphicsScene, QGraphicsPixmapItem,
    QVBoxLayout, QPushButton, QWidget, QGridLayout, QHBoxLayout,
    QLabel, QScrollArea, QSizePolicy, QMessageBox, QFrame,
    QStackedWidget, QTreeView, QMainWindow
)
from PyQt6.QtGui import QPixmap, QColor, QPainter, QFont, \
    QStandardItemModel, QStandardItem, QAction
from PyQt6.QtCore import Qt
import sys
import add_projection as add_projection
import add_space as add_space
import add_thing_projection
import draggable_pixmap_item as draggable_item
import utils as utils
import image_container
import space
import zoomable_graphics_view
import projection as pr
import projection_container as container
from track_object_state import ObjectState
import image as im
import add_image
import add_thing
import thing

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

        self.background = None
        self.background_item = None
        self.parent_space = None

        self.x_scale = None
        self.y_scale = None

        self.mini_projections_list = []


        self.stack_widget = QStackedWidget()

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
        self.layout_images = QVBoxLayout()
        self.layout_images_of_space = QHBoxLayout()

        self.scroll_for_images = QScrollArea()
        self.scroll_for_images.setWidgetResizable(True)
        self.scroll_for_images.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.scroll_for_images.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        #scroll_for_images.setWidgetResizable(True)
        #scroll_for_images.adjustSize()
        #scroll_for_images.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

        #self.layout_projections = QVBoxLayout()

        self.layout_projections_of_space = QVBoxLayout()

        self.container_projections_of_space = QWidget()  # контейнер для развертки

        self.scroll_for_projections_of_space = QScrollArea()
        self.scroll_for_projections_of_space.setWidgetResizable(True)
        self.scroll_for_projections_of_space.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.container_projections_of_space.setLayout(self.layout_projections_of_space)
        self.container_projections_of_space.adjustSize()
        self.scroll_for_projections_of_space.setWidget(self.container_projections_of_space)

        self.layout_projections = QVBoxLayout()

        self.add_new_space_projection_button = QPushButton("Add new space projection")
        self.add_new_space_projection_button.clicked.connect(self.add_new_space_projection)

        self.layout_projections.addWidget(self.scroll_for_projections_of_space)
        self.layout_projections.addWidget(self.add_new_space_projection_button)

        #self.layout_projections_of_space.addWidget(self.add_new_space_projection_button)


        #self.add_image_of_space_button = QPushButton("Add image of space")
        #self.add_image_of_space_button.clicked.connect(self.add_image_of_space)

        self.container_images_of_space.setLayout(self.layout_images_of_space)
        self.container_images_of_space.adjustSize()
        self.scroll_for_images.setWidget(self.container_images_of_space)
        #layout_images_of_space.setContentsMargins(0, 0, 0, 0)
        #scroll_for_images.setContentsMargins(0, 0, 0, 0)
        #scroll_for_images.adjustSize()
        self.layout_images.addLayout(self.layout_images_of_space)
        #self.layout_images.addWidget(self.add_image_of_space_button)


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

        self.add_thing_button = QPushButton("Добавить вещь в пространство")
        self.add_thing_button.clicked.connect(self.add_thing)

        self.add_image_of_space_button = QPushButton("Add image of space")
        self.add_image_of_space_button.clicked.connect(self.add_image_of_space)

        self.save_space_button = QPushButton("Save space")
        self.save_space_button.clicked.connect(self.save_space_to_DB)

        self.save_current_projection_button = QPushButton("Save current projection")
        self.save_current_projection_button.clicked.connect(self.save_current_projection)

        self.button_layout.addWidget(self.add_projection_of_space_button)
        self.button_layout.addWidget(self.add_subspace_button)
        self.button_layout.addWidget(self.save_current_projection_button)
        self.button_layout.addWidget(self.save_space_button)
        self.button_layout.addWidget(self.add_thing_button)

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

        self.layout_images.addWidget(self.scroll_for_images)
        self.layout_images.addWidget(self.add_image_of_space_button)

        self.layout_main.addLayout(self.layout_images, 2, 0)  # , 1, 2)###################################
        #self.layout_main.addWidget(self.scroll_for_images, 2, 0)#, 1, 2)###################################
        self.layout_main.setRowStretch(2, 2)

        #self.left_view_frame = QFrame()
        #self.left_view_layout

        self.tree = QTreeView()
        #self.model = QStandardItemModel()
        #model.setHorizontalHeaderLabels(["Название", "Описание"])
        #self.tree.setModel(self.model)
        #self.tree.expandAll()


        #self.left_layout = QHBoxLayout()

        self.right_layout.addLayout(self.layout_projections, 0, 0)
        #self.right_layout.addWidget(self.scroll_for_projections_of_space, 0, 0)
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

                if subspace.state != ObjectState.DELETED:
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
                    self.parent_space = space.Space(dict_of_new_space["name"])
                    self.parent_space.mark_new()

                    if dict_of_new_space["description"]:
                        self.parent_space.description = dict_of_new_space["description"]

                    self.current_index = 1
                    self.stack_widget.setCurrentIndex(self.current_index)

                    self.update_tree_view()

                    break  # успех — выходим из цикла

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

                    is_name_busy = False
                    if self.parent_space.projections:
                        is_name_busy = any(projection.projection_name == projection_name for projection in self.parent_space.projections)

                    if not is_name_busy:

                        # Добавление новой картинки
                        if self.parent_space.current_projection is None:

                            original_image = temp_dict_new_space_projection["image"]

                            scaled_image = utils.calculate_new_image_size(
                                original_image,
                                temp_dict_new_space_projection["x_sm"],
                                temp_dict_new_space_projection["y_sm"]
                            )

                            scaled_cropped_pixmap = utils.get_scaled_pixmap(
                                original_image,
                                scaled_image.width(),
                                scaled_image.height()
                            )

                            self.x_scale = scaled_cropped_pixmap.width() / temp_dict_new_space_projection["x_sm"]
                            self.y_scale = scaled_cropped_pixmap.height() / temp_dict_new_space_projection["y_sm"]

                            new_projection = pr.Projection(temp_dict_new_space_projection["name"],
                                                       original_image,
                                                       temp_dict_new_space_projection["x_sm"],
                                                       temp_dict_new_space_projection["y_sm"],
                                                       self.parent_space,
                                                       scaled_projection_pixmap=scaled_cropped_pixmap)
                            new_projection.mark_new()

                            if temp_dict_new_space_projection["description"]:
                                new_projection.projection_description = temp_dict_new_space_projection["description"]

                            self.parent_space.projections.append(new_projection)

                            self.parent_space.current_projection = new_projection

                            self.set_background(scaled_cropped_pixmap)

                            #TODO при загрузке бублика появляются scrollbar и размер view слишком большой
                            print(f"view_w: {self.view.width()}")
                            print(f"view_h: {self.view.height()}")

                            self.add_projection_of_space_button.setText("Change space projection")

                            break

                        # Замена существующей фоновой картинки и других данных о развертке

                        #TODO пересчет размеров подразверток при изменении размера развертки

                        else:
                            print(f"???????????????????_self.parent_space.current_projection: {self.parent_space.current_projection}")
                            temp_dict_new_space_projection = add_projection_dialog.get_data()

                            original_image = temp_dict_new_space_projection["image"]
                            scaled_image = utils.calculate_new_image_size(
                                original_image,
                                temp_dict_new_space_projection["x_sm"],
                                temp_dict_new_space_projection["y_sm"]
                            )

                            scaled_cropped_pixmap = utils.get_scaled_pixmap(
                                original_image,
                                scaled_image.width(),
                                scaled_image.height()
                            )

                            self.x_scale = scaled_cropped_pixmap.width() / temp_dict_new_space_projection["x_sm"]
                            self.y_scale = scaled_cropped_pixmap.height() / temp_dict_new_space_projection["y_sm"]

                            self.parent_space.current_projection.projection_image \
                                = original_image
                            self.parent_space.current_projection.x_sm \
                                = temp_dict_new_space_projection["x_sm"]
                            self.parent_space.current_projection.y_sm \
                                = temp_dict_new_space_projection["y_sm"]
                            self.parent_space.current_projection.projection_name \
                                = temp_dict_new_space_projection["name"]
                            if temp_dict_new_space_projection["description"]:
                                self.parent_space.current_projection.projection_description \
                                    = temp_dict_new_space_projection["description"]

                            self.parent_space.current_projection.reset_state()

                            self.set_background(scaled_cropped_pixmap)

                            if self.parent_space.current_projection.sub_projections:
                                for subproj in self.parent_space.current_projection.sub_projections:
                                    subproj.scaled_projection_pixmap.update_path(self.background)

                            break

                    else:
                        QMessageBox.warning(self, "Имя занято", "Такое имя уже существует. Пожалуйста, введите другое.")
                        # не очищаем — пользователь увидит свои прежние данные

                        break
            else:
                break  # пользователь нажал "Отмена" — выходим


    def set_background(self, scaled_cropped_pixmap):
        if self.placeholder_for_projection:
            self.scene.removeItem(self.placeholder_for_projection)
            self.placeholder_for_projection = None

        if self.background_item:
            self.scene.removeItem(self.background_item)
            self.background_item = None

        self.background = QPixmap(scaled_cropped_pixmap)
        self.background_item = QGraphicsPixmapItem(self.background)

        min_z = min((item.zValue() for item in self.scene.items()), default=0)

        self.background_item.setZValue(min_z - 1)  # Отправляем фон на самый задний план
        self.background_item.setPos(0, 0)
        self.scene.addItem(self.background_item)
        self.view.fitInView(self.background_item, Qt.AspectRatioMode.KeepAspectRatio)



    def add_subspace(self):
        add_subspace_dialog = add_space.AddSpace()

        while True:
            if add_subspace_dialog.exec():
                dict_of_new_space = add_subspace_dialog.get_data()

                if not dict_of_new_space["name"]:
                    QMessageBox.warning(self, "Заполните обязательные поля",
                                        "Пожалуйста укажите название пространства!")
                else:
                    new_space = space.Space(dict_of_new_space["name"], dict_of_new_space["description"])
                    new_space.mark_new()

                    self.parent_space.subspaces.append(new_space)

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

                    is_projection_name_busy = False
                    if self.parent_space.current_projection.sub_projections:
                        is_projection_name_busy = next((name for name in self.parent_space.current_projection.sub_projections
                                                        if name.projection_name == projection_name), None)

                    if not is_projection_name_busy:
                        original_image = temp_dict_new_subspace_projection["image"]
                        print(f"original_image_sub.width: {original_image.width()}")
                        print(f"original_image_sub.height: {original_image.height()}")

                        pixmap = utils.get_scaled_pixmap(
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


                        new_sub_projection = pr.Projection(
                            temp_dict_new_subspace_projection["name"],
                            original_image,temp_dict_new_subspace_projection["x_sm"],
                            temp_dict_new_subspace_projection["y_sm"],
                            reference_to_parent_space=subspace
                        )
                        new_sub_projection.mark_new()

                        # родитель подразвертки это развертка, которая на данный момент отображается как background
                        new_sub_projection.reference_to_parent_projection = self.parent_space.current_projection

                        item = draggable_item.DraggablePixmapItem(pixmap, self.scene, self, self.background, parent=subspace)

                        new_sub_projection.scaled_projection_pixmap = item

                        if temp_dict_new_subspace_projection["description"]:
                            new_sub_projection.projection_description = temp_dict_new_subspace_projection["description"]

                        self.parent_space.current_projection.sub_projections.append(new_sub_projection)

                        item.setPos(0, 0)
                        item.old_pos = item.pos()
                        self.scene.addItem(item)

                        break  # успех — выходим из цикла
                    else:
                        QMessageBox.warning(self, "Имя занято", "Такое имя уже существует. Пожалуйста, введите другое.")
                        # не очищаем — пользователь увидит свои прежние данные
            else:
                break  # пользователь нажал "Отмена" — выходим


    def add_thing(self):
        add_thing_dialog = add_thing.AddThing()

        while True:
            if add_thing_dialog.exec():
                dict_of_new_space = add_thing_dialog.get_data()

                if not dict_of_new_space["name"]:
                    QMessageBox.warning(self, "Заполните обязательные поля",
                                        "Пожалуйста укажите название вещи!")
                else:
                    new_thing = thing.Thing(dict_of_new_space["name"], self.parent_space)
                    new_thing.mark_new()

                    if dict_of_new_space["description"]:
                        new_thing.description = dict_of_new_space["description"]

                    if dict_of_new_space["image"]:
                        new_thing.image = dict_of_new_space["image"]

                    self.parent_space.things.append(new_thing)
                    print(f"self.parent_space.things: {self.parent_space.things}")

                    self.add_thing_projection(new_thing)

                    #self.update_tree_view()

                    break  # успех — выходим из цикла

            else:
                break  # пользователь нажал "Отмена" — выходим


    def add_thing_projection(self, new_thing: thing.Thing):
        if not self.parent_space.current_projection:
            QMessageBox.warning(self, "Добавьте проекцию пространства",
                                "Если хотите также добавить проекцию вещи, то "
                                "необходимо вначале добавить проекцию пространства!")
            return

        add_thing_projection_dialog = add_thing_projection.AddThingProjection()

        while True:
            if add_thing_projection_dialog.exec():
                temp_dict_new_thing_projection = add_thing_projection_dialog.get_data()

                if not temp_dict_new_thing_projection["name"]:
                    QMessageBox.warning(self, "Заполните обязательные поля",
                                        "Пожалуйста укажите название вещи!")
                elif not temp_dict_new_thing_projection["image"]:
                    QMessageBox.warning(self, "Заполните обязательные поля",
                                        "Пожалуйста загрузите изображение проекции!")
                else:
                    original_image = temp_dict_new_thing_projection["image"]

                    scaled_pixmap = utils.get_scaled_pixmap(
                        temp_dict_new_thing_projection["image"],
                        int(round(self.x_scale * temp_dict_new_thing_projection["x_sm"])),
                        int(round(self.y_scale * temp_dict_new_thing_projection["y_sm"]))
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


                    new_thing_projection = pr.Projection(
                        temp_dict_new_thing_projection["name"],
                        original_image,
                        temp_dict_new_thing_projection["x_sm"],
                        temp_dict_new_thing_projection["y_sm"],
                        # родитель подразвертки это развертка, которая на данный момент отображается как background
                        reference_to_parent_projection=self.parent_space.current_projection,
                        reference_to_parent_thing=new_thing
                    )
                    new_thing_projection.mark_new()

                    item = draggable_item.DraggablePixmapItem(scaled_pixmap, self.scene, self, self.background, parent=new_thing)

                    new_thing_projection.scaled_projection_pixmap = item

                    if temp_dict_new_thing_projection["description"]:
                        new_thing_projection.projection_description = temp_dict_new_thing_projection["description"]

                    new_thing.projections.append(new_thing_projection)

                    item.setPos(0, 0)
                    item.old_pos = item.pos()
                    self.scene.addItem(item)

                    break  # успех — выходим из цикла

            else:
                break  # пользователь нажал "Отмена" — выходим


    def add_image_of_space(self):
        add_image_dialog = add_image.AddImage()

        while True:
            if add_image_dialog.exec():
                image = add_image_dialog.get_data()

                if not image["image"]:
                    QMessageBox.warning(self, "Заполните обязательные поля",
                                        "Пожалуйста загрузите изображение пространства!")
                else:

                    new_image = im.SpaceImage(
                        image["image"],
                        image["name"]
                    )
                    new_image.mark_new()

                    self.parent_space.space_images.append(new_image)

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

                    for item in self.parent_space.space_images:

                        image_widget = image_container.ImageContainer(item, self.container_images_of_space.contentsRect().height())
                        image_widget.delete_image.connect(self.delete_image)

                        if not image_widget.space_image.state == ObjectState.DELETED:
                            self.layout_images_of_space.addWidget(image_widget)
                        self.layout_images_of_space.setAlignment(Qt.AlignmentFlag.AlignLeft)
                    break
            else:
                break


    def delete_image(self, image):

        if image in self.parent_space.space_images:
            if image.state == ObjectState.NEW:
                # Просто удаляю, потому что он ещё не сохранён в БД
                self.parent_space.space_images.remove(image)
            else:
                # Помечаю на удаление
                image.mark_deleted()


    def add_new_space_projection(self):

        if self.placeholder_for_projection:
            self.scene.removeItem(self.placeholder_for_projection)
            self.placeholder_for_projection = None
            self.add_space_projection()
            return

        is_saved = True
        if self.mini_projections_list:
            is_saved = next((mini for mini in self.mini_projections_list if
                             mini.saved_projection == self.parent_space.current_projection), None)

        if not is_saved:
            QMessageBox.warning(self, "Сохранить текущую развертку", "Текущая развертка не сохранена!")
            return

        if self.background_item:
            self.scene.removeItem(self.background_item)
            self.background = None
            self.background_item = None

        if self.parent_space.current_projection:
            if self.parent_space.current_projection.sub_projections:
                for sub_projection in self.parent_space.current_projection.sub_projections:
                    self.scene.removeItem(sub_projection.scaled_projection_pixmap)

        if self.parent_space.current_projection:
            self.parent_space.current_projection = None
        self.add_space_projection()


    def update_mini_projections_layout(self):
        utils.clear_layout(self.layout_projections_of_space)
        for widget in self.mini_projections_list:
            if widget.saved_projection.state != ObjectState.DELETED:
                self.layout_projections_of_space.addWidget(widget)
        self.layout_projections_of_space.setAlignment(Qt.AlignmentFlag.AlignTop)


    def save_current_projection(self):
        if not self.background_item:
            QMessageBox.warning(self, "Развёртка отсутствует", "У Вас нет развертки для сохранения!")
            return
        else:
            if self.parent_space.current_projection:
                if self.parent_space.current_projection.sub_projections:
                    for sub_projection in self.parent_space.current_projection.sub_projections:
                        if sub_projection.state != ObjectState.DELETED:
                            item = sub_projection.scaled_projection_pixmap
                            if item is None or self.background_item is None:
                                continue
                            relative_pos = self.background_item.mapFromItem(item, 0, 0)
                            sub_projection.x_pos = relative_pos.x()
                            sub_projection.y_pos = relative_pos.y()

            # Если мини проекция уже сохранена, то обновляем её вид
            mini_projection_to_change = next((mini for mini in self.mini_projections_list if
                                              mini.saved_projection == self.parent_space.current_projection), None)
            if mini_projection_to_change:
                print(f"self.parent_space.current_projection:")
                mini_projection_to_change.update_scene(self.parent_space.current_projection)
                self.update_mini_projections_layout()

            # Если мини проекция не сохранена, то сохраняем
            else:
                new_mini_projection = container.ProjectionContainer(
                    self.parent_space.current_projection,
                    self
                )
                self.mini_projections_list.insert(0, new_mini_projection)
                self.update_mini_projections_layout()


    def delete_mini_projection(self, mini_projection):

        mini_projection_to_remove = next((mini for mini in self.mini_projections_list if mini == mini_projection),
                                         None)
        if mini_projection_to_remove:
            projection = next((projection for projection in self.parent_space.projections
                               if projection == mini_projection_to_remove.saved_projection), None)

            if projection == self.parent_space.current_projection:
                self.parent_space.current_projection = None
                self.background = None
                self.background_item = None
                self.scene.clear()

            if projection:
                if projection.state == ObjectState.NEW:
                    self.parent_space.projections.remove(projection)
                else:
                    projection.mark_deleted()

        self.mini_projections_list.remove(mini_projection_to_remove)
        self.update_mini_projections_layout()

        # Удаляем вещь из self.things
        # Удаляем все проекции со всех сцен (главная сцена, сцены мини разверток)
    def delete_thing(self):
        pass


        # При удалении подпространства необходимо удалить
        # его подразвертку из self.sub_projections
        # и его пространство из self.subspaces и также саму картинку со сцены

    def delete_subspace(self, draggable_item_pointer):
        # Находим объект Projection, связанный с изображением
        subprojection_to_remove = next(
            (projection for projection in self.parent_space.current_projection.sub_projections
             if projection.scaled_projection_pixmap == draggable_item_pointer),
            None
        )
        print(subprojection_to_remove.state)

        # Находим связанный subspace
        subspace_to_remove = next(
            (subspace for subspace in self.parent_space.subspaces
             if subspace == subprojection_to_remove.reference_to_parent_space),
            None
        )
        print(subspace_to_remove.state)

        # Удаляем subspace с учётом его состояния
        if subspace_to_remove:
            if subspace_to_remove.state == ObjectState.NEW:
                self.parent_space.subspaces.remove(subspace_to_remove)
            else:
                subspace_to_remove.mark_deleted()

            self.tree.update()

        # Удаляем projection с учётом его состояния
        if subprojection_to_remove:
            if subprojection_to_remove.state == ObjectState.NEW:
                self.parent_space.current_projection.sub_projections.remove(subprojection_to_remove)
            else:
                subprojection_to_remove.mark_deleted()


    def save_space_to_DB(self):

        self.save_current_projection()

        self.parent_space.save_space()


    def open_space(self):
        pass


    def load_space_from_DB(self):
        pass
        #self.parent_space = space.Space()




if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())