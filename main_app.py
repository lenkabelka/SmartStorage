import random
import decimal

from PyQt6.QtWidgets import (
    QApplication, QGraphicsScene, QGraphicsPixmapItem,
    QVBoxLayout, QPushButton, QWidget, QGridLayout, QHBoxLayout,
    QScrollArea, QSizePolicy, QMessageBox, QFrame, QStackedWidget,
    QMainWindow, QGraphicsTextItem, QGraphicsView
)
from PyQt6.QtGui import QFont, QAction
from PyQt6.QtCore import Qt, QPointF, pyqtSignal
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
import mini_projection_container as container
from track_object_state import ObjectState
import image as im
import add_image
import add_thing
import thing
import tree_view
import all_spaces_in_DB
import tree_view_for_search


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Smart Storage")
        menu = self.menuBar()

        self.action_create_new_space = QAction("Создать новое пространство", self)
        self.action_open_space = QAction("Открыть пространство ...", self)
        self.action_save_space = QAction("Сохранить пространство ...", self)
        self.action_show_full_structure_of_space = QAction("Показать всё дерево пространства", self)
        self.action_exit = QAction("Закрыть программу", self)
        self.action_delete_space = QAction("Удалить пространство", self)


        menu.setStyleSheet("""
            QMenuBar {
                background-color: #f0f0f0;
                border-bottom: 1px solid #888;
            }
        """)

        file_menu = menu.addMenu("&File")
        about_menu = menu.addMenu("&About")
        file_menu.addAction(self.action_create_new_space)
        file_menu.addAction(self.action_open_space)
        file_menu.addAction(self.action_save_space)
        file_menu.addAction(self.action_show_full_structure_of_space)
        file_menu.addAction(self.action_exit)
        file_menu.addSeparator()
        file_menu.addAction(self.action_delete_space)


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

        self.main_widget = MainWidget()
        self.setCentralWidget(self.main_widget)

        self.action_save_space.triggered.connect(lambda: print("Меню сохранения нажато"))
        self.action_save_space.triggered.connect(self.main_widget.save_space_to_DB)

        self.action_open_space.triggered.connect(self.main_widget.load_space_from_db_by_selection_from_spaces_list)

        self.action_show_full_structure_of_space.triggered.connect(self.main_widget.show_full_structure_of_space)

        self.action_create_new_space.triggered.connect(self.main_widget.create_new_space)
        self.action_exit.triggered.connect(self.close_application)

        self.main_widget.space_changed.connect(self.update_actions)

        self.update_actions()

    def update_actions(self):
        parent_space = self.main_widget.parent_space
        self.action_save_space.setEnabled(
            parent_space is not None and getattr(parent_space, "state", None) != ObjectState.DELETED
        )
        self.action_delete_space.setEnabled(
            parent_space is not None and getattr(parent_space, "state", None) != ObjectState.DELETED
        )
        self.action_show_full_structure_of_space.setEnabled(
            parent_space is not None and getattr(parent_space, "state", None) != ObjectState.DELETED
        )

    def close_application(self):
        QApplication.quit()


class MainWidget(QWidget):
    space_changed = pyqtSignal()

    def __init__(self):
        super().__init__()

        self.parent_space = None
        self.x_scale = None
        self.y_scale = None

        self.mini_projections_list = []

        self.stack_widget = QStackedWidget()

############## wellcome page ###########################################################################################
        self.wellcome_page = QFrame()
        self.wellcome_layout = QVBoxLayout()

        wellcome_scene = QGraphicsScene()
        wellcome_view = QGraphicsView(wellcome_scene)
        font_size = int(min(wellcome_view.width(), wellcome_view.height()) * 0.03)
        font = QFont("Arial", font_size)

        # Первый текст
        wellcome_placeholder = QGraphicsTextItem(
            "Добро пожаловать в программу умного хранения вещей!"
        )
        wellcome_placeholder.setFont(font)
        wellcome_placeholder_rect = wellcome_placeholder.boundingRect()
        wellcome_placeholder.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        wellcome_scene.addItem(wellcome_placeholder)

        self.add_space_button = QPushButton("Создать новое пространство")
        self.open_saved_space_button = QPushButton("Открыть пространство ...")

        self.wellcome_layout.addWidget(wellcome_view)
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

        self.add_new_space_projection_button = QPushButton("Добавить новую проекцию пространства")
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



        # self.pixmap_placeholder = QPixmap(300, 300)
        #
        # painter = QPainter(self.pixmap_placeholder)
        # painter.setPen(QColor("white"))
        # painter.setFont(QFont("Arial", 20))
        # painter.drawText(self.pixmap_placeholder.rect(), Qt.AlignmentFlag.AlignCenter, "Hello!")
        # painter.end()
        #
        # self.placeholder_for_projection = QGraphicsPixmapItem(self.pixmap_placeholder)


        self.scene = QGraphicsScene(self)
        self.view = zoomable_graphics_view.ZoomableGraphicsView(self.scene)

        # Первый текст
        self.placeholder_for_projection_1 = QGraphicsTextItem(
            "Добавьте сюда проекцию пространства, кликнув правой кнопкой мыши на"
        )

        # Второй текст
        self.placeholder_for_projection_2 = QGraphicsTextItem(
            "пространстве в списке справа, или нажав на кнопку \"Добавить новую проекцию пространства\"."
        )

        self.set_placeholders_on_main_scene()

        # int(min(wellcome_view.width(), wellcome_view.height()) * 0.03)
        # font = QFont("Arial", font_size)
        #
        # # Первый текст
        # self.placeholder_for_projection_1 = QGraphicsTextItem(
        #     "Добавьте сюда проекцию пространства, кликнув правой кнопкой мыши на"
        # )
        # self.placeholder_for_projection_1.setFont(font)
        # line1_rect =self.placeholder_for_projection_1.boundingRect()
        #
        # # Второй текст
        # self.placeholder_for_projection_2 = QGraphicsTextItem(
        #     "пространстве в списке справа, или нажав на кнопку \"Добавить новую проекцию пространства\"."
        # )
        # self.placeholder_for_projection_2.setFont(font)
        # line2_rect = self.placeholder_for_projection_2.boundingRect()
        #
        # # Общая высота
        # total_height = line1_rect.height() + line2_rect.height()
        # center_y = (self.scene.height() - total_height) / 2
        #
        # # Устанавливаем позиции по центру
        # self.placeholder_for_projection_1.setPos((self.scene.width() - line1_rect.width()) / 2, center_y)
        # self.placeholder_for_projection_2.setPos((self.scene.width() - line2_rect.width()) / 2, center_y
        #                                          + line1_rect.height())
        #
        # self.placeholder_for_projection_1.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        # self.placeholder_for_projection_2.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        #
        # self.scene.addItem(self.placeholder_for_projection_1)
        # self.scene.addItem(self.placeholder_for_projection_2)
        #
        #
        #
        # #self.scene.addItem(self.placeholder_for_projection)
        # self.view.setScene(self.scene)
        #self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        #self.view.setSceneRect(0, 0, 800, 600)

        self.button_layout = QVBoxLayout()

        #self.add_projection_of_space_button = QPushButton("Add projection of space")
        ##############self.add_projection_of_space_button.clicked.connect(self.add_projection_of_space)
        #self.add_projection_of_space_button.clicked.connect(self.add_space_projection)

        #self.add_subspace_button = QPushButton("Add subspace")
        #self.add_subspace_button.clicked.connect(self.add_subspace)

        #self.add_projection_of_subspace_button = QPushButton("Add projection of subspace")
        #self.add_projection_of_subspace_button.clicked.connect(self.add_projection_of_subspace)

        #self.add_thing_button = QPushButton("Добавить вещь в пространство")
        #self.add_thing_button.clicked.connect(self.add_thing)

        self.add_image_of_space_button = QPushButton("Добавить фотографию пространства")
        self.add_image_of_space_button.clicked.connect(self.add_image_of_space)

        #self.save_space_button = QPushButton("Save space")
        #self.save_space_button.clicked.connect(self.save_space_to_DB)

        self.save_current_projection_button = QPushButton("Сохранить проекцию")
        self.save_current_projection_button.clicked.connect(lambda: self.save_or_update_mini_projection(self.parent_space.current_projection))

        #self.button_layout.addWidget(self.add_projection_of_space_button)
        #self.button_layout.addWidget(self.add_subspace_button)
        self.button_layout.addWidget(self.save_current_projection_button)
        #self.button_layout.addWidget(self.save_space_button)
        #self.button_layout.addWidget(self.add_thing_button)

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

        self.tree = tree_view.TreeWidget(self)

        self.tree_view_of_full_space_structure = tree_view_for_search.TreeWidget(self)

        #self.tree = QTreeView()
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


    def set_placeholders_on_main_scene(self):
        font_size = int(min(self.view.width(), self.view.height()) * 0.03)
        font = QFont("Arial", font_size)

        # Первый текст
        self.placeholder_for_projection_1 = QGraphicsTextItem(
            "Добавьте сюда проекцию пространства, кликнув правой кнопкой мыши на"
        )

        self.placeholder_for_projection_1.setFont(font)
        line1_rect =self.placeholder_for_projection_1.boundingRect()

        # Второй текст
        self.placeholder_for_projection_2 = QGraphicsTextItem(
            "пространстве в списке справа, или нажав на кнопку \"Добавить новую проекцию пространства\"."
        )

        self.placeholder_for_projection_2.setFont(font)
        line2_rect = self.placeholder_for_projection_2.boundingRect()

        # Общая высота
        total_height = line1_rect.height() + line2_rect.height()
        center_y = (self.scene.height() - total_height) / 2

        # Устанавливаем позиции по центру
        self.placeholder_for_projection_1.setPos((self.scene.width() - line1_rect.width()) / 2, center_y)
        self.placeholder_for_projection_2.setPos((self.scene.width() - line2_rect.width()) / 2, center_y
                                                 + line1_rect.height())

        self.placeholder_for_projection_1.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.placeholder_for_projection_2.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        self.scene.addItem(self.placeholder_for_projection_1)
        self.scene.addItem(self.placeholder_for_projection_2)

        self.view.setScene(self.scene)

        bounding_rect = self.scene.itemsBoundingRect()
        self.scene.setSceneRect(bounding_rect)

        self.view.fitInView(bounding_rect, Qt.AspectRatioMode.KeepAspectRatio)


    def update_tree_view(self):
        self.tree.update_tree(self.parent_space)


    def update_app_state(self):
        self.update_main_scene()
        self.update_mini_projections_layout()
        self.update_tree_view()
        if self.parent_space.space_images:
            self.clear_layout(self.parent_space.space_images)


    def create_new_space(self):
        if self.parent_space is None:
            self.add_space()
        else:
            if self.parent_space.state == ObjectState.NEW or self.parent_space.state == ObjectState.MODIFIED:
                reply = QMessageBox.question(
                    self,
                    "Сохранить пространство",
                    "Пространство не сохранено!\nХотите сохранить пространство?",
                    QMessageBox.StandardButton.Yes
                    | QMessageBox.StandardButton.No
                    | QMessageBox.StandardButton.Cancel,
                    QMessageBox.StandardButton.Cancel
                )

                if reply == QMessageBox.StandardButton.Yes:
                    self.save_space_to_DB()
                    self.update_app_state()
                    self.add_space()

                elif reply == QMessageBox.StandardButton.No:
                    self.update_app_state()
                    self.add_space()

                elif reply == QMessageBox.StandardButton.Cancel:
                    return
            else:
                self.update_app_state()
                self.add_space()


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

                    self.space_changed.emit()

                    self.set_buttons_disabled_or_enabled()

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

                            scaled_cropped_pixmap = utils.get_scaled_cropped_pixmap(
                                temp_dict_new_space_projection["image"],
                                temp_dict_new_space_projection["x_sm"],
                                temp_dict_new_space_projection["y_sm"]
                            )

                            self.set_x_and_y_scales(
                                scaled_cropped_pixmap,
                                temp_dict_new_space_projection["x_sm"],
                                temp_dict_new_space_projection["y_sm"]
                            )

                            new_projection = pr.Projection(temp_dict_new_space_projection["name"],
                                                       original_image,
                                                       scaled_cropped_pixmap,
                                                       temp_dict_new_space_projection["x_sm"],
                                                       temp_dict_new_space_projection["y_sm"],
                                                       self.parent_space,
                                                       scaled_projection_pixmap=QGraphicsPixmapItem(scaled_cropped_pixmap))
                            new_projection.mark_new()

                            if temp_dict_new_space_projection["description"]:
                                new_projection.projection_description = temp_dict_new_space_projection["description"]

                            self.parent_space.current_projection = new_projection

                            self.update_main_scene()

                            break

                        # Замена существующей фоновой картинки и других данных о развертке
                        else:
                            temp_dict_new_space_projection = add_projection_dialog.get_data()
                            original_image = temp_dict_new_space_projection["image"]

                            scaled_cropped_pixmap = utils.get_scaled_cropped_pixmap(
                                temp_dict_new_space_projection["image"],
                                temp_dict_new_space_projection["x_sm"],
                                temp_dict_new_space_projection["y_sm"]
                            )
                            self.set_x_and_y_scales(
                                scaled_cropped_pixmap,
                                temp_dict_new_space_projection["x_sm"],
                                temp_dict_new_space_projection["y_sm"]
                            )

                            self.parent_space.current_projection.projection_image \
                                = original_image
                            self.parent_space.current_projection.original_pixmap \
                                = scaled_cropped_pixmap
                            self.parent_space.current_projection.scaled_projection_pixmap \
                                = QGraphicsPixmapItem(scaled_cropped_pixmap)
                            self.parent_space.current_projection.x_sm \
                                = temp_dict_new_space_projection["x_sm"]
                            self.parent_space.current_projection.y_sm \
                                = temp_dict_new_space_projection["y_sm"]
                            self.parent_space.current_projection.projection_name \
                                = temp_dict_new_space_projection["name"]
                            if temp_dict_new_space_projection["description"]:
                                self.parent_space.current_projection.projection_description \
                                    = temp_dict_new_space_projection["description"]

                            self.update_main_scene(set_position=False)

                            if self.parent_space.current_projection.sub_projections:
                                for subproj in self.parent_space.current_projection.sub_projections:
                                    print(f"subproj.scaled_projection_pixmap: {subproj.scaled_projection_pixmap}")
                                    subproj.scaled_projection_pixmap.update_path(self.parent_space.current_projection.scaled_projection_pixmap)

                            break

                    else:
                        QMessageBox.warning(self, "Имя занято", "Такое имя уже существует. Пожалуйста, введите другое.")
                        # не очищаем — пользователь увидит свои прежние данные
                        break
            else:
                break  # пользователь нажал "Отмена" — выходим


    def set_x_and_y_scales(self, scaled_cropped_pixmap, real_projection_width, real_projection_height):
        self.x_scale = scaled_cropped_pixmap.width() / real_projection_width
        self.y_scale = scaled_cropped_pixmap.height() / real_projection_height


    def update_main_scene(self, set_position=None):
        if self.scene.items():
            self.scene.clear()
            self.placeholder_for_projection_1 = None
            self.placeholder_for_projection_2 = None

        if self.parent_space.current_projection is not None:
            self.parent_space.current_projection.scaled_projection_pixmap \
                = QGraphicsPixmapItem(self.parent_space.current_projection.original_pixmap)
            min_z = min((item.zValue() for item in self.scene.items()), default=0)
            self.parent_space.current_projection.scaled_projection_pixmap.setZValue(min_z - 1)  # Отправляем фон на самый задний план
            self.scene.addItem(self.parent_space.current_projection.scaled_projection_pixmap)

            if self.parent_space.current_projection.sub_projections:
                for sub in self.parent_space.current_projection.sub_projections:
                    if sub.state is not ObjectState.DELETED:
                        parent = None
                        if sub.reference_to_parent_thing:
                            parent = sub.reference_to_parent_thing
                        elif sub.reference_to_parent_space:
                            parent = sub.reference_to_parent_space
                        # перерасчет размеров подразверток на основании новых размеров пространства,
                        # а также на основании новых размеров картинки:
                        pixmap = utils.get_scaled_pixmap(
                            sub.projection_image,
                            int(round(self.x_scale * sub.projection_width)),
                            int(round(self.y_scale * sub.projection_height))
                        )
                        sub.original_pixmap = pixmap
                        sub.scaled_projection_pixmap = draggable_item.DraggablePixmapItem(
                            pixmap,
                            self,
                            self.parent_space.current_projection.scaled_projection_pixmap,
                            parent=parent)
                        if sub.z_pos:
                            sub.scaled_projection_pixmap.setZValue(sub.z_pos)

                        # необходимо при открытии мини-развертки на главное сцене
                        if set_position:
                            if sub.x_pos and sub.y_pos:
                                sub.scaled_projection_pixmap.setPos(sub.x_pos, sub.y_pos)
                        else:
                            # теперь подпроекции будут появляться в середине сцены
                            #center = self.scene.sceneRect().center()
                            center = self.parent_space.current_projection.scaled_projection_pixmap.boundingRect().center()
                            sub_rect = sub.scaled_projection_pixmap.boundingRect()
                            offset = QPointF(sub_rect.width() / 2, sub_rect.height() / 2)
                            sub.scaled_projection_pixmap.setPos(center - offset)
                            # # Так как это может быть совершенно новое пространство, с другими размерами
                            # # то не целесообразно использовать sub.x_pos and sub.y_pos.
                            # # В дальнейшем можно спросить пользователя, остаётся ли пространство с теми же
                            # # размерами или нет.
                            # if sub.x_pos and sub.y_pos:
                            #     sub.scaled_projection_pixmap.setPos(sub.x_pos, sub.y_pos)
                        self.scene.addItem(sub.scaled_projection_pixmap)

            bounding_rect = self.scene.itemsBoundingRect()
            self.scene.setSceneRect(bounding_rect)

            self.view.fitInView(bounding_rect, Qt.AspectRatioMode.KeepAspectRatio)

        else:
            self.set_placeholders_on_main_scene()


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


    def add_subspace_projection(self, subspace_to_add_projection: space.Space):
        if not self.parent_space.current_projection:
            QMessageBox.warning(self, "Добавьте проекцию пространства",
                                "Если хотите также добавить проекцию подпространства, то "
                                "необходимо вначале добавить проекцию пространства!")
            return

        if self.parent_space.current_projection.sub_projections:
            for subprojection in self.parent_space.current_projection.sub_projections:
                if subprojection.reference_to_parent_space == subspace_to_add_projection:
                    QMessageBox.warning(self, "Запрет добавления проекции",
                                        "На одну проекцию пространства можно добавить "
                                        "только одну проекцию для одного и того же подпространства")

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
                elif self.parent_space.current_projection.projection_width <= temp_dict_new_subspace_projection["x_sm"] \
                        or self.parent_space.current_projection.projection_height <= temp_dict_new_subspace_projection["y_sm"]:
                    QMessageBox.warning(self, "Подпространство больше пространства",
                                        "Подпространство не может быть больше пространства!")

                else:

                    projection_name = temp_dict_new_subspace_projection["name"]

                    is_projection_name_busy = False
                    if self.parent_space.current_projection.sub_projections:
                        is_projection_name_busy = next((name for name in self.parent_space.current_projection.sub_projections
                                                        if name.projection_name == projection_name), None)

                    if not is_projection_name_busy:
                        original_image = temp_dict_new_subspace_projection["image"]

                        pixmap = utils.get_scaled_pixmap(
                            temp_dict_new_subspace_projection["image"],
                            int(round(self.x_scale * temp_dict_new_subspace_projection["x_sm"])),
                            int(round(self.y_scale * temp_dict_new_subspace_projection["y_sm"]))
                        )

                        new_sub_projection = pr.Projection(
                            temp_dict_new_subspace_projection["name"],
                            original_image,
                            pixmap,
                            temp_dict_new_subspace_projection["x_sm"],
                            temp_dict_new_subspace_projection["y_sm"],
                            reference_to_parent_space=subspace_to_add_projection
                        )
                        new_sub_projection.mark_new()

                        # родитель подразвертки это развертка, которая на данный момент отображается как background
                        new_sub_projection.reference_to_parent_projection = self.parent_space.current_projection

                        item = draggable_item.DraggablePixmapItem(pixmap, self, self.parent_space.current_projection.scaled_projection_pixmap, parent=subspace_to_add_projection)

                        new_sub_projection.scaled_projection_pixmap = item

                        if temp_dict_new_subspace_projection["description"]:
                            new_sub_projection.projection_description = temp_dict_new_subspace_projection["description"]

                        self.parent_space.current_projection.sub_projections.append(new_sub_projection)
                        subspace_to_add_projection.projections.append(new_sub_projection)

                        # теперь подпроекции будут появляться в середине сцены
                        center = self.scene.sceneRect().center()
                        item_rect = item.boundingRect()
                        offset = QPointF(item_rect.width() / 2, item_rect.height() / 2)
                        item.setPos(center - offset)

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

                    self.update_tree_view()

                    break  # успех — выходим из цикла

            else:
                break  # пользователь нажал "Отмена" — выходим


    def add_thing_projection(self, thing_to_add_projection: thing.Thing):
        if not self.parent_space.current_projection:
            QMessageBox.warning(self, "Добавьте проекцию пространства",
                                "Если хотите также добавить проекцию вещи, то "
                                "необходимо вначале добавить проекцию пространства!")
            return

        if self.parent_space.current_projection.sub_projections:
            for subprojection in self.parent_space.current_projection.sub_projections:
                if subprojection.reference_to_parent_thing == thing_to_add_projection:
                    QMessageBox.warning(self, "Запрет добавления проекции",
                                        "На одну проекцию пространства можно добавить "
                                        "только одну проекцию для одной и той же  вещи")

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

                    new_thing_projection = pr.Projection(
                        temp_dict_new_thing_projection["name"],
                        original_image,
                        scaled_pixmap,
                        temp_dict_new_thing_projection["x_sm"],
                        temp_dict_new_thing_projection["y_sm"],
                        # родитель подразвертки это развертка, которая на данный момент отображается как background
                        reference_to_parent_projection=self.parent_space.current_projection,
                        reference_to_parent_thing=thing_to_add_projection
                    )
                    new_thing_projection.mark_new()

                    item = draggable_item.DraggablePixmapItem(
                        scaled_pixmap,
                        self,
                        self.parent_space.current_projection.scaled_projection_pixmap,
                        parent=thing_to_add_projection
                    )

                    new_thing_projection.scaled_projection_pixmap = item

                    if temp_dict_new_thing_projection["description"]:
                        new_thing_projection.projection_description = temp_dict_new_thing_projection["description"]

                    self.parent_space.current_projection.sub_projections.append(new_thing_projection)

                    # теперь подпроекции будут появляться в середине сцены
                    center = self.scene.sceneRect().center()
                    item_rect = item.boundingRect()
                    offset = QPointF(item_rect.width() / 2, item_rect.height() / 2)
                    item.setPos(center - offset)

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
                    self.update_images_layout()

                    break
            else:
                break

    def clear_layout(self, layout):
        for i in reversed(range(layout.count())):
            item = layout.takeAt(i)  # <-- обязательно удалить из layout
            if item is not None:
                widget = item.widget()
                if widget:
                    widget.setParent(None)  # <-- отключить от layout
                    widget.deleteLater()  # <-- пометить на удаление
                else:
                    sublayout = item.layout()
                    if sublayout:
                        self.clear_layout(sublayout)


    def update_images_layout(self):
        self.clear_layout(self.layout_images_of_space)

        for item in self.parent_space.space_images:

            image_widget = image_container.ImageContainer(item, self.container_images_of_space.contentsRect().height())
            image_widget.delete_image.connect(self.delete_image)

            if not image_widget.space_image.state == ObjectState.DELETED:
                self.layout_images_of_space.addWidget(image_widget)
            self.layout_images_of_space.setAlignment(Qt.AlignmentFlag.AlignLeft)


    def delete_image(self, image):
        if image in self.parent_space.space_images:
            if image.state == ObjectState.NEW:
                self.parent_space.space_images.remove(image)
            else:
                image.mark_deleted()


    def is_main_scene_equal_to_mini_scene(self, mini):
        def sort_key(item):
            return item.zValue(), item.pos().x(), item.pos().y()

        items_main = sorted(self.scene.items(), key=sort_key)
        items_mini = sorted(mini.scene.items(), key=sort_key)

        if len(items_main) != len(items_mini):
            print("len не равны")
            return False

        for item_main, item_mini in zip(items_main, items_mini):
            # QGraphicsPixmapItem и DraggablePixmapItem в данном случае будут сравниваться, как равные
            if not isinstance(item_main, QGraphicsPixmapItem) or not isinstance(item_mini, QGraphicsPixmapItem):
                print("типы не равны")
                return False

            if item_main.pos() != item_mini.pos():
                print("позиции не равны")
                return False

            if item_main.zValue() != item_mini.zValue():
                print("Z не равны")
                return False

        return True


    def is_current_projection_saved(self):
        mini_projection = next((mini for mini in self.mini_projections_list
                         if mini.saved_projection == self.parent_space.current_projection), None)
        if mini_projection:
            is_main_scene_equal_to_mini_scene = self.is_main_scene_equal_to_mini_scene(mini_projection)
            return is_main_scene_equal_to_mini_scene
        else:
            return False


    def add_new_space_projection(self):
        if self.placeholder_for_projection_1 and self.placeholder_for_projection_2:
            self.scene.removeItem(self.placeholder_for_projection_1)
            self.scene.removeItem(self.placeholder_for_projection_2)
            self.placeholder_for_projection_1 = None
            self.placeholder_for_projection_2 = None
            self.add_space_projection()
            return

        is_current_projection_saved = self.is_current_projection_saved()

        if is_current_projection_saved:
            self.scene.clear()
            self.parent_space.current_projection = None
            self.add_space_projection()
        elif not self.scene.items():
            self.parent_space.current_projection = None
            self.add_space_projection()
        else:
            reply = QMessageBox.question(
                self,
                "Сохранить текущую развертку",
                "Текущая развертка не сохранена!\nХотите сохранить текущую развертку?",
                QMessageBox.StandardButton.Yes
                | QMessageBox.StandardButton.No
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.save_or_update_mini_projection(self.parent_space.current_projection)
                self.parent_space.current_projection = None
                self.add_space_projection()

            elif reply == QMessageBox.StandardButton.No:
                self.scene.clear()
                self.parent_space.current_projection = None
                self.add_space_projection()

            elif reply == QMessageBox.StandardButton.Cancel:
                return


    def update_mini_projections_layout(self):
        utils.clear_layout(self.layout_projections_of_space)

        current_projection = next((mini_projection for mini_projection in self.mini_projections_list
                                   if mini_projection.saved_projection == self.parent_space.current_projection), None)

        # то, что отображено на главной сцене в виджете мини сцен будет на самом верху
        if current_projection:
            self.mini_projections_list.remove(current_projection)
            self.mini_projections_list.insert(0, current_projection)

        for widget in self.mini_projections_list:
            if widget.saved_projection.state != ObjectState.DELETED:
                self.layout_projections_of_space.addWidget(widget)
        self.layout_projections_of_space.setAlignment(Qt.AlignmentFlag.AlignTop)


    def save_or_update_mini_projection(self, current_projection):
        if self.placeholder_for_projection_1 and self.placeholder_for_projection_2:
            QMessageBox.warning(self, "Развёртка отсутствует", "У Вас нет развертки для сохранения!")
            return

        if self.parent_space.current_projection:
            if not self.parent_space.current_projection.scaled_projection_pixmap:
                QMessageBox.warning(self, "Развёртка отсутствует", "У Вас нет развертки для сохранения!")
                return
            else:
                self.get_subprojection_position()
                # if self.parent_space.current_projection.sub_projections:
                #     for sub_projection in self.parent_space.current_projection.sub_projections:
                #         if sub_projection.state != ObjectState.DELETED:
                #             item = sub_projection.scaled_projection_pixmap
                #             if item is None or self.parent_space.current_projection.scaled_projection_pixmap is None:
                #                 continue
                #             relative_pos = self.parent_space.current_projection.scaled_projection_pixmap.mapFromItem(item, 0, 0)
                #             sub_projection.x_pos = relative_pos.x()
                #             sub_projection.y_pos = relative_pos.y()
                #             sub_projection.z_pos = item.zValue()

                # Если мини проекция уже сохранена, то, если нужно, обновляем её вид
                mini_projection_to_change = next((mini for mini in self.mini_projections_list if
                                                  mini.saved_projection == current_projection), None)
                if mini_projection_to_change:
                    if not self.is_main_scene_equal_to_mini_scene(mini_projection_to_change):
                        mini_projection_to_change.update_scene(current_projection)
                        self.update_mini_projections_layout()

                # Если мини проекция не сохранена, то сохраняем её
                # (также добавляем её в self.parent_space.projections.
                # Если пользователь нажмет "сохранить пространство",
                # то в БД сохранятся те развертки, которые были ранее
                # сохранены, как мини-развертки)
                else:
                    new_mini_projection = container.ProjectionContainer(
                        current_projection,
                        self
                    )

                    self.parent_space.projections.append(self.parent_space.current_projection)

                    self.mini_projections_list.insert(0, new_mini_projection)
                    print(self.mini_projections_list)
                    self.update_mini_projections_layout()


    def get_subprojection_position(self):
        if self.parent_space.current_projection.sub_projections:
            for sub_projection in self.parent_space.current_projection.sub_projections:
                if sub_projection.state != ObjectState.DELETED:
                    item = sub_projection.scaled_projection_pixmap
                    if item is None or self.parent_space.current_projection.scaled_projection_pixmap is None:
                        continue
                    relative_pos = self.parent_space.current_projection.scaled_projection_pixmap.mapFromItem(item, 0, 0)
                    sub_projection.x_pos = relative_pos.x()
                    sub_projection.y_pos = relative_pos.y()
                    sub_projection.z_pos = item.zValue()


    def delete_mini_projection(self, mini_projection):

        mini_projection_to_remove = next((mini for mini in self.mini_projections_list if mini == mini_projection),
                                         None)
        if mini_projection_to_remove:
            projection = next((projection for projection in self.parent_space.projections
                               if projection == mini_projection_to_remove.saved_projection), None)

            if projection == self.parent_space.current_projection:
                self.parent_space.current_projection = None
                self.scene.clear()

            if projection:
                if projection.state == ObjectState.NEW:
                    self.parent_space.projections.remove(projection)
                else:
                    projection.mark_deleted()

        self.mini_projections_list.remove(mini_projection_to_remove)
        self.update_mini_projections_layout()


    def set_mini_projection_on_main_scene(self, mini_projection):
        mini_projection_to_set_on_scene = next((mini for mini in self.mini_projections_list if mini == mini_projection),
                                         None)
        if mini_projection_to_set_on_scene:
            projection = next((projection for projection in self.parent_space.projections
                               if projection == mini_projection_to_set_on_scene.saved_projection), None)

            if projection:
                self.parent_space.current_projection = projection

                self.set_x_and_y_scales(
                    self.parent_space.current_projection.original_pixmap,
                    self.parent_space.current_projection.projection_width,
                    self.parent_space.current_projection.projection_height
                )

                self.update_main_scene(set_position=True)
                self.update_mini_projections_layout()


    def delete_one_subprojection(self, draggable_item_pointer):
        # удаление одной подразвертки подпространства или вещи происходит всегда на текущей развёртке пространства
        if self.parent_space.current_projection:
            if self.parent_space.current_projection.sub_projections:

                subprojection_to_remove = next((sub for sub in self.parent_space.current_projection.sub_projections
                                                if sub.scaled_projection_pixmap == draggable_item_pointer), None)
                if subprojection_to_remove:
                    if subprojection_to_remove.state == ObjectState.NEW:
                        self.parent_space.current_projection.sub_projections.remove(subprojection_to_remove)
                    else:
                        subprojection_to_remove.mark_deleted()

                    self.get_subprojection_position() # чтобы другие подразвертки не сдвигались,
                                                      # изначально у них сохраненнвя позиция та, что в БД
                    self.update_main_scene(set_position=True)


    def delete_all_subprojections(self, draggable_item_pointer):

        if self.parent_space.current_projection:
            if self.parent_space.current_projection.sub_projections:
                subprojection = next((sub for sub in self.parent_space.current_projection.sub_projections
                                      if sub.scaled_projection_pixmap == draggable_item_pointer), None)

                if subprojection:
                    if subprojection.reference_to_parent_space:
                        parent_of_subprojection = subprojection.reference_to_parent_space

                        for projection in self.parent_space.projections:
                            subprojection_to_remove = next((sub for sub in projection.sub_projections
                                                            if sub.reference_to_parent_space == parent_of_subprojection), None)
                            if subprojection_to_remove:
                                if subprojection_to_remove.state == ObjectState.NEW:
                                    projection.sub_projections.remove(subprojection_to_remove)
                                else:
                                    subprojection_to_remove.mark_deleted()

                    elif subprojection.reference_to_parent_thing:
                        parent_of_subprojection = subprojection.reference_to_parent_thing

                        for projection in self.parent_space.projections:
                            subprojection_to_remove = next((sub for sub in projection.sub_projections
                                                            if sub.reference_to_parent_thing == parent_of_subprojection), None)
                            if subprojection_to_remove:
                                if subprojection_to_remove.state == ObjectState.NEW:
                                    projection.sub_projections.remove(subprojection_to_remove)
                                else:
                                    subprojection_to_remove.mark_deleted()

                    # Тут может быть два сценария:
                    # 1. Если текущая развертка была сохранена в мини развертку,
                    # то она была добавлена в projections у parent_space -> в данном случае при удалении подразвертки
                    # из развертки у parent_space, она автоматически будет удалена из current_projection.
                    # 2. В случае, если current_projection не была сохранена в мини сцены (она не была добавлена
                    # в projections у parent_space), то подразвертка не удалится в current_projection
                    # и её надо удалить дополнительно из current_projection

                    subprojection_to_remove_in_current_projection \
                        = next((sub for sub in self.parent_space.current_projection.sub_projections
                                if sub == subprojection), None)
                    if subprojection_to_remove_in_current_projection:
                        self.parent_space.current_projection.sub_projections.remove(subprojection_to_remove_in_current_projection)

            self.get_subprojection_position()  # чтобы другие подразвертки не сдвигались,
            # изначально у них сохраненнвя позиция та, что в БД
            self.update_main_scene(set_position=True)
            for proj in self.parent_space.projections:
                self.save_or_update_mini_projection(proj)


    def delete_thing(self, thing_to_delete):
        thing_to_remove = next((thg for thg in self.parent_space.things if thg == thing_to_delete))
        if thing_to_remove:
            if thing_to_remove.state == ObjectState.NEW:
                self.parent_space.things.remove(thing_to_remove)
            else:
                thing_to_remove.mark_deleted()

            if self.parent_space.current_projection:
                if self.parent_space.current_projection.sub_projections:
                    sub_projection = next((sub for sub in self.parent_space.current_projection.sub_projections
                                   if sub.reference_to_parent_thing == thing_to_remove), None)

                    if sub_projection:
                        self.delete_all_subprojections(sub_projection.scaled_projection_pixmap)

            self.update_tree_view()


    def delete_subspace(self, subspace_to_delete):
        subspace_to_remove = next((sub for sub in self.parent_space.subspaces if sub == subspace_to_delete))
        if subspace_to_remove:
            if subspace_to_remove.state == ObjectState.NEW:
                self.parent_space.subspaces.remove(subspace_to_remove)
            else:
                subspace_to_remove.mark_deleted()

            if self.parent_space.current_projection:
                if self.parent_space.current_projection.sub_projections:
                    sub_projection = next((sub for sub in self.parent_space.current_projection.sub_projections
                                   if sub.reference_to_parent_space == subspace_to_remove), None)

                    if sub_projection:
                        self.delete_all_subprojections(sub_projection.scaled_projection_pixmap)

            self.update_tree_view()


    def delete_space(self, space_to_delete):
        if self.parent_space == space_to_delete:

            if self.parent_space.state == ObjectState.NEW:
                self.parent_space = None
            else:
                self.parent_space.mark_deleted()
                if self.parent_space.projections:
                    for proj in self.parent_space.projections:
                        proj.mark_deleted()
                        if proj.sub_projections:
                            for subproj in proj.sub_projections:
                                subproj.mark_deleted()
                if self.parent_space.subspaces:
                    for sub in self.parent_space.subspaces:
                        sub.mark_deleted()
                if self.parent_space.things:
                    for item in self.parent_space.things:
                        item.mark_deleted()
                if self.parent_space.space_images:
                    for image in self.parent_space.space_images:
                        image.mark_deleted()

            self.clear_layout(self.layout_images_of_space)
            self.scene.clear()
            self.placeholder_for_projection_1 = None
            self.placeholder_for_projection_2 = None
            self.mini_projections_list.clear()
            self.update_mini_projections_layout()
            self.update_tree_view()
            self.space_changed.emit()
            self.set_buttons_disabled_or_enabled()
            self.set_placeholders_on_main_scene()

            if self.parent_space is not None:
                self.parent_space.save_space()


    def save_space_to_DB(self):
        if self.mini_projections_list:
            is_current_projection_saved = self.is_current_projection_saved()

            if is_current_projection_saved and self.mini_projections_list:
                self.parent_space.save_space()
            else:
                reply = QMessageBox.question(
                    self,
                    "Сохранить текущую развертку",
                    "Текущая развертка не сохранена!\nХотите сохранить текущую развертку?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )

                if reply == QMessageBox.StandardButton.Yes:
                    self.save_or_update_mini_projection(self.parent_space.current_projection)
                    self.parent_space.save_space()
                elif reply == QMessageBox.StandardButton.No:
                    self.parent_space.save_space()
        else:
            self.parent_space.save_space()

        self.show_full_structure_of_space()


    def open_space(self, space_to_open: space.Space):
        # TODO проверять, сохранено ли текущее пространство self.parent_space

        # открываю подпространство как пространство
            # этого пространства ещё нет в базе
        self.parent_space = space_to_open

        if self.parent_space.projections:
            self.parent_space.current_projection = random.choice(self.parent_space.projections)

            self.update_main_scene()
            self.update_tree_view()
            self.mini_projections_list.clear()

            for proj in self.parent_space.projections:
                self.save_or_update_mini_projection(proj)
            self.update_mini_projections_layout()

        self.update_tree_view()
        self.update_main_scene()
        self.mini_projections_list = []
        self.update_mini_projections_layout()


    def load_space_from_DB(self, id_space):
        loaded_space = space.load_space_by_id(id_space)

        self.parent_space = loaded_space

        if self.current_index == 0:
            self.current_index = 1
            self.stack_widget.setCurrentIndex(self.current_index)

        self.update_tree_view()
        self.update_images_layout()

        if self.parent_space.projections:
            # выбираем как главную развёртку ту, у которой самое большое количество подразверток или,
            # если подразвёрток ни у одной развертки нет, то первую в списке projections
            self.parent_space.current_projection = max(self.parent_space.projections,
                                                       key=lambda p: len(p.sub_projections))
            self.x_scale = (self.parent_space.current_projection.original_pixmap.width()
                            / self.parent_space.current_projection.projection_width)
            self.y_scale = (self.parent_space.current_projection.original_pixmap.height()
                            / self.parent_space.current_projection.projection_height)

            print(type(self.x_scale))

            for proj in self.parent_space.projections:
                for subproj in proj.sub_projections:

                    if subproj.id_parent_thing:
                        subproj.reference_to_parent_thing = next((thing_item for thing_item in self.parent_space.things
                                                                  if thing_item.id_thing == subproj.id_parent_thing),
                                                                 None)
                    elif subproj.id_parent_space:
                        subproj.reference_to_parent_space = next(
                            (space_item for space_item in self.parent_space.subspaces
                             if space_item.id_space == subproj.id_parent_space), None)

            self.update_main_scene(True)

            for proj in self.parent_space.projections:
                self.save_or_update_mini_projection(proj)

        self.space_changed.emit()
        self.set_buttons_disabled_or_enabled()


    def load_parent_space_from_DB(self):
        if self.parent_space.id_parent_space is not None:
            self.load_space_from_DB(self.parent_space.id_parent_space)
        else:
            QMessageBox.warning(self, "Родительское пространство отсутствует", "Для этого пространства "
                                                                               "нет родительского пространства!")


    def load_space_from_db_by_selection_from_spaces_list(self):
        spaces_in_DB = all_spaces_in_DB.load_all_spaces_from_DB()

        if spaces_in_DB is None:
            QMessageBox.warning(self, "Нет пространств", "В базе данных пока нет ни одного пространства!")
            return

        spaces_list = all_spaces_in_DB.SpacesList(spaces_in_DB)

        def on_selected(row):
            print(f"Выбранная строка: {row}")

            if self.mini_projections_list:
                self.mini_projections_list.clear()

            # получаю id_space выбранного пространства
            id_space = spaces_in_DB[row][0]

            self.load_space_from_DB(id_space)

        spaces_list.spaceDoubleClicked.connect(on_selected)

        if spaces_list.exec():
            print("Диалог закрыт с accept")
        else:
            print("Диалог закрыт без выбора")


    def show_full_structure_of_space(self):
        if self.parent_space.state != ObjectState.NEW:

            if self.parent_space.id_parent_space:
                id_top_space = space.get_top_space_id(self.parent_space.id_parent_space)
            else:
                id_top_space = self.parent_space.id_space

            top_space = space.load_space_by_id(id_top_space)

            #tree_view_of_full_space_structure = tree_view_for_search.TreeWidget(self)
            self.tree_view_of_full_space_structure.update_tree(top_space)
            self.tree_view_of_full_space_structure.show()

        else:
            QMessageBox.warning(self, "Новое пространство", "Это пространство новое, его структура "
                                                            "уже показана полностью в дереве справа!")


    def set_buttons_disabled_or_enabled(self):
        if self.parent_space is None or self.parent_space.state == ObjectState.DELETED:
            self.add_image_of_space_button.setEnabled(False)
            self.add_new_space_projection_button.setEnabled(False)
            self.save_current_projection_button.setEnabled(False)
        else:
            self.add_image_of_space_button.setEnabled(True)
            self.add_new_space_projection_button.setEnabled(True)
            self.save_current_projection_button.setEnabled(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())