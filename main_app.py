from PyQt6.QtWidgets import (
    QGraphicsScene, QGraphicsPixmapItem,
    QVBoxLayout, QPushButton, QWidget, QGridLayout, QHBoxLayout,
    QScrollArea, QSizePolicy, QMessageBox, QFrame, QStackedWidget,
    QMainWindow, QGraphicsTextItem, QGraphicsDropShadowEffect, QDialog, QApplication
)
from PyQt6.QtGui import QFont, QAction, QPixmap, QIcon, QColor, QPainter, QTransform, QPainterPath
from PyQt6.QtCore import Qt, QPoint, QPointF, pyqtSignal, QRectF
import sys
import random
import add_projection as add_projection
import add_space as add_space
import draggable_pixmap_item as draggable_item
import find_thing
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
import main_scene
import log_in as log
import user as usr
import access_manager as ac


class MainWindow(QMainWindow):
    def __init__(self, user: usr.User):
        super().__init__()

        self.user = user

        self.main_widget = MainWidget(self.user)
        self.setCentralWidget(self.main_widget)

        self.setWindowTitle("Smart Storage")
        self.setWindowIcon(QIcon("icons/mini_logo.png"))
        self.menu = self.menuBar()

        self.action_find_thing = QAction("Найти вещь", self)
        self.action_create_new_space = QAction("Создать новое пространство", self)
        self.action_open_space = QAction("Открыть пространство ...", self)
        self.action_save_space = QAction("Сохранить пространство ...", self)
        self.action_show_full_structure_of_space = QAction("Показать всё дерево пространства", self)
        self.action_exit = QAction("Закрыть программу", self)
        self.action_delete_space = QAction("Удалить пространство", self)

        self.menu.setStyleSheet("""
            QMenuBar {
                background-color: #f0f0f0;
                border-bottom: 3px solid #888;
            }
        """)

        file_menu = self.menu.addMenu("&Файл")
        about_menu = self.menu.addMenu("&О программе")
        file_menu.addAction(self.action_find_thing)
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

        #self.main_widget = MainWidget()
        #self.setCentralWidget(self.main_widget)

        self.action_find_thing.triggered.connect(self.main_widget.find_thing)
        self.action_save_space.triggered.connect(lambda: print("Меню сохранения нажато"))
        self.action_save_space.triggered.connect(self.main_widget.save_space_to_DB)
        self.action_open_space.triggered.connect(self.main_widget.load_space_from_db_by_selection_from_spaces_list)
        self.action_show_full_structure_of_space.triggered.connect(self.main_widget.show_full_structure_of_space)
        self.action_create_new_space.triggered.connect(self.main_widget.create_new_space)
        self.action_exit.triggered.connect(self.close) # метод close() вызовет closeEvent
        self.action_delete_space.triggered.connect(self.main_widget.delete_space)
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


    def closeEvent(self, event):
        try:
            if self.main_widget.is_space_saved():
                event.accept()

            else:
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
                    if self.main_widget.mini_projections_list:
                        if not self.main_widget.is_current_projection_saved():
                            (self.main_widget.save_or_update_mini_projection
                                (self.main_widget.parent_space.current_projection,
                                check_permissions=False
                                )
                            )
                    self.main_widget.save_space_to_DB()
                    self.main_widget.tree_view_of_full_space_structure.close()
                    event.accept()

                elif reply == QMessageBox.StandardButton.No:
                    event.accept()

                elif reply == QMessageBox.StandardButton.Cancel:
                    event.ignore()

        except Exception as e:
            print(f"Ошибка при сохранении: {e}")
            event.ignore()


class MainWidget(QWidget):
    space_changed = pyqtSignal()

    def __init__(self, user: usr.User):
        super().__init__()

        self.user = user

        self.access_manager = ac.AccessManager(self.user)


        self.parent_space = None
        self.x_scale = None
        self.y_scale = None

        self.mini_projections_list = []

        self.stack_widget = QStackedWidget()

        self.thing_info = None
        self.space_info = None

        self.all_things_in_space_scroll = QScrollArea()
        self.all_things_in_space_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

############## wellcome page ###########################################################################################
        self.wellcome_page = QFrame()
        self.wellcome_layout = QVBoxLayout()

        self.wellcome_scene = QGraphicsScene()
        self.wellcome_view = zoomable_graphics_view.ZoomableGraphicsView(self.wellcome_scene) #QGraphicsView(wellcome_scene)

        self.wellcome_placeholder_pixmap = QPixmap("icons/LOGO_1.png")
        self.wellcome_placeholder = QGraphicsPixmapItem(self.wellcome_placeholder_pixmap)
        self.wellcome_scene.addItem(self.wellcome_placeholder)
        self.wellcome_scene.setSceneRect(self.wellcome_scene.itemsBoundingRect())

        self.update_placeholder_of_wellcome_view()

        self.wellcome_layout.addWidget(self.wellcome_view)

        self.wellcome_page.setLayout(self.wellcome_layout)

        self.wellcome_view.resized.connect(self.update_placeholder_of_wellcome_view)

############## opened space page ###########################################################################################

        self.create_or_change_space = QFrame()

        self.layout_main = QGridLayout()

        self.left_layout = QVBoxLayout()
        self.right_layout = QGridLayout()#QHBoxLayout()

        self.layout_space_creation = QVBoxLayout()
        self.container_images_of_space = QWidget()

        self.layout_images = QVBoxLayout()
        self.layout_images_of_space = QHBoxLayout()

        self.scroll_for_images = QScrollArea()
        self.scroll_for_images.setWidgetResizable(True)
        self.scroll_for_images.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.scroll_for_images.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
##################
        self.layout_projections_of_space = QVBoxLayout()

        self.container_projections_of_space = QWidget()  # контейнер для развертки

        self.scroll_for_projections_of_space = QScrollArea()
        self.scroll_for_projections_of_space.setWidgetResizable(True)
        self.scroll_for_projections_of_space.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.container_projections_of_space.setLayout(self.layout_projections_of_space)
        self.container_projections_of_space.adjustSize()
        self.scroll_for_projections_of_space.setWidget(self.container_projections_of_space)

        self.layout_projections = QVBoxLayout()

        self.add_new_space_projection_button = QPushButton("Добавить новую проекцию пространства")
        #self.add_new_space_projection_button.setStyleSheet(sheet)
        self.add_new_space_projection_button.clicked.connect(self.add_new_space_projection)

        self.layout_projections.addWidget(self.scroll_for_projections_of_space)
        self.layout_projections.addWidget(self.add_new_space_projection_button)
#####################
        self.container_images_of_space.setLayout(self.layout_images_of_space)
        self.container_images_of_space.adjustSize()
        self.scroll_for_images.setWidget(self.container_images_of_space)

        self.layout_images.addLayout(self.layout_images_of_space)

        self.button_layout = QVBoxLayout()

        self.add_image_of_space_button = QPushButton("Добавить фотографию пространства")
        self.add_image_of_space_button.clicked.connect(self.add_image_of_space)

        self.save_current_projection_button = QPushButton("Сохранить проекцию")
        self.save_current_projection_button.clicked.connect(lambda: self.save_or_update_mini_projection(self.parent_space.current_projection))

        self.button_layout.addWidget(self.save_current_projection_button)


        #self.scene = QGraphicsScene(self)
        self.scene = main_scene.MainScene(self)
        self.view = zoomable_graphics_view.ZoomableGraphicsView(self.scene)
        self.view.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Рендеринг высокого качества
        self.view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        self.view.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)

        self.layout_space_creation.addWidget(self.view)

        self.layout_main.addLayout(self.layout_space_creation, 0, 0)#, 3, 2)
        self.layout_main.setRowStretch(0, 4)

        self.layout_main.addLayout(self.button_layout, 1, 0)
        self.layout_main.setRowStretch(1, 1)

        self.layout_images.addWidget(self.scroll_for_images)
        self.layout_images.addWidget(self.add_image_of_space_button)

        self.layout_main.addLayout(self.layout_images, 2, 0)

        self.layout_main.setRowStretch(2, 2)

        self.tree = tree_view.TreeWidget(self)


        #self.tree.node_clicked.connect(self.handle_node_clicked)

        self.scene.draggable_item_click.connect(lambda draggable: self.tree.highlight_node(draggable))


        self.tree.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.tree_view_of_full_space_structure = tree_view_for_search.TreeWidgetForSearch(self)

        self.right_layout.addLayout(self.layout_projections, 0, 0)
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

        self.placeholder_for_projection_1 = None
        self.placeholder_for_projection_2 = None
        self.set_placeholders_on_main_scene()

        self.view.resized.connect(self.update_placeholders_font_and_position)
        self.view.resized.connect(self.update_scene_size)

        self._open_space_windows = []

        self.information_about_things = []
        self.found_things_tree_views = []
        self.information_about_spaces = []

        self.offset_for_found_things_trees = 0


    def find_thing(self):
        try:
            find_thing_dialog = find_thing.FindThing(self, self.user.id, self.user.role)

            while True:
                if find_thing_dialog.exec():
                    parameters_for_search = find_thing_dialog.get_parameters_for_search()
                    print(f"parameters_for_search: {parameters_for_search}")

                    if not parameters_for_search[0]:
                        QMessageBox.warning(self, "Заполните обязательные поля",
                                            "Пожалуйста укажите ключевые слова для поиска вещи!")
                    elif not parameters_for_search[3]:
                        QMessageBox.warning(self, "Заполните обязательные поля",
                                            "Пожалуйста укажите пространства для поиска вещи!")

                    else:
                        found_things = find_thing_dialog.find_thing_in_DB()

                        if found_things:
                            for found_thing in found_things:
                                print(found_thing[3])
                                top_space_of_thing = self.show_space_of_thing(found_thing[3], found_thing[1])
                                print(top_space_of_thing)
                            print(found_things)
                        else:
                            QMessageBox.warning(self, "Ничего не найдено",
                                                "Ничего не найдено!")

                        break  # успех — выходим из цикла

                else:
                    break  # пользователь нажал "Отмена" — выходим
        except Exception as e:
            print(e)

    def create_new_space(self):

        """
        Создаёт новое пространство с учётом прав пользователя.
        Если текущее пространство не сохранено, запрашивает у пользователя подтверждение на сохранение.
        В зависимости от ответа сохраняет или пропускает сохранение текущего пространства
        и вызывает add_space() для создания нового пространства.
        """

        try:
            if self.user is None:
                raise ValueError("Невозможно создать пространство: пользователь не указан")

            # Проверка прав (для совместимости, вдруг потом добавятся роли)
            # Сейчас — любой пользователь может создать новое пространство, для
            # которого станет editor
            if self.user.role not in ("admin", "user"):
                raise PermissionError("Ваш тип пользователя не позволяет создавать пространства")

            # Основная логика создания нового пространства
            add_space_accepted = False
            if self.parent_space is None or self.parent_space.state == ObjectState.UNMODIFIED:
                add_space_accepted = self.add_space()
            else:
            #if self.parent_space.state in (ObjectState.NEW, ObjectState.MODIFIED):
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
                    #self.update_app_view()
                    add_space_accepted = self.add_space()

                elif reply == QMessageBox.StandardButton.No:
                    #self.update_app_view()
                    add_space_accepted = self.add_space()

                elif reply == QMessageBox.StandardButton.Cancel:
                    return

            if add_space_accepted:
                self.update_app_view()

        except PermissionError as e:
            QMessageBox.warning(self, "Нет прав", str(e))
        except ValueError as e:
            QMessageBox.critical(self, "Ошибка данных", str(e))
        except Exception as e:
            print(f"Unexpected error: {e}")
            QMessageBox.critical(self, "Ошибка", "Произошла непредвиденная ошибка. Обратитесь к администратору.")


    def add_space(self):

        add_space_dialog = add_space.AddSpace()

        if add_space_dialog.exec():
            dict_of_new_space = add_space_dialog.get_data()

            self.parent_space = space.Space(name=dict_of_new_space["name"])
            self.parent_space.mark_new()

            if dict_of_new_space["description"]:
                self.parent_space.description = dict_of_new_space["description"]

            self.current_index = 1
            self.stack_widget.setCurrentIndex(self.current_index)

            #self.update_tree_view()

            self.space_changed.emit()

            self.set_buttons_disabled_or_enabled()

            return True

        else:
            return False


    def add_space_projection(self):
        try:
            if self.user is None:
                raise ValueError("Невозможно добавить проекцию: пользователь не указан")

            # Проверка прав доступа
            if not self.access_manager.can_edit(self.parent_space):
                raise PermissionError("У вас нет прав для добавления или изменения проекции этого пространства")

            # --- Основная логика добавления / замены проекции ---
            add_projection_dialog = add_projection.AddProjection(projection_parent=self.parent_space)

            while True:

                if self.parent_space.current_projection is not None:
                    # --------------
                    # Передаём текущие данные в диалог, чтобы они отобразились при вызове "изменить проекцию"
                    add_projection_dialog.name_edit.setText(self.parent_space.current_projection.projection_name)
                    add_projection_dialog.description_edit.setText(
                        self.parent_space.current_projection.projection_description)
                    add_projection_dialog.x_width.setText(str(self.parent_space.current_projection.projection_width))
                    add_projection_dialog.y_height.setText(str(self.parent_space.current_projection.projection_height))

                    if self.parent_space.current_projection.projection_image:
                        add_projection_dialog.image = self.parent_space.current_projection.projection_image
                        add_projection_dialog.set_image()
                    # --------------

                if add_projection_dialog.exec(): # тут вернется ADialog.Accepted, равное или 1, или 0

                    temp_dict_new_space_projection = add_projection_dialog.get_data()
                    projection_name = temp_dict_new_space_projection["name"]

                    is_name_busy = False
                    if self.parent_space.projections:
                        is_name_busy = any(
                            projection.projection_name == projection_name
                            for projection in self.parent_space.projections
                        )

                    if is_name_busy:
                        QMessageBox.warning(self, "Имя занято",
                                            "Такое имя уже существует. Пожалуйста, введите другое.")
                    else:

                        # --- Добавление новой картинки ---
                        if self.parent_space.current_projection is None:
                            original_image = temp_dict_new_space_projection["image"]

                            scaled_cropped_pixmap = utils.get_scaled_cropped_pixmap(
                                temp_dict_new_space_projection["image"],
                                temp_dict_new_space_projection["x_width"],
                                temp_dict_new_space_projection["y_height"]
                            )

                            self.set_x_and_y_scales(
                                scaled_cropped_pixmap,
                                temp_dict_new_space_projection["x_width"],
                                temp_dict_new_space_projection["y_height"]
                            )

                            new_projection = pr.Projection(
                                temp_dict_new_space_projection["name"],
                                original_image,
                                scaled_cropped_pixmap,
                                temp_dict_new_space_projection["x_width"],
                                temp_dict_new_space_projection["y_height"],
                                self.parent_space,
                                scaled_projection_pixmap=QGraphicsPixmapItem(scaled_cropped_pixmap)
                            )
                            new_projection.mark_new()

                            if temp_dict_new_space_projection["description"]:
                                new_projection.projection_description = temp_dict_new_space_projection["description"]

                            self.parent_space.current_projection = new_projection
                            self.parent_space.current_projection.z_pos = -1
                            self.update_main_scene()

                        # --- Замена существующей картинки ---
                        else:
                            # Обновляем данные
                            temp_dict_new_space_projection = add_projection_dialog.get_data()
                            original_image = temp_dict_new_space_projection["image"]

                            scaled_cropped_pixmap = utils.get_scaled_cropped_pixmap(
                                temp_dict_new_space_projection["image"],
                                temp_dict_new_space_projection["x_width"],
                                temp_dict_new_space_projection["y_height"]
                            )
                            self.set_x_and_y_scales(
                                scaled_cropped_pixmap,
                                temp_dict_new_space_projection["x_width"],
                                temp_dict_new_space_projection["y_height"]
                            )

                            self.parent_space.current_projection.projection_image = original_image
                            self.parent_space.current_projection.original_pixmap = scaled_cropped_pixmap
                            self.parent_space.current_projection.scaled_projection_pixmap = QGraphicsPixmapItem(
                                scaled_cropped_pixmap)
                            self.parent_space.current_projection.x_width = temp_dict_new_space_projection["x_width"]
                            self.parent_space.current_projection.y_height = temp_dict_new_space_projection["y_height"]
                            self.parent_space.current_projection.projection_name = temp_dict_new_space_projection["name"]
                            if temp_dict_new_space_projection["description"]:
                                self.parent_space.current_projection.projection_description = \
                                    temp_dict_new_space_projection["description"]

                            self.parent_space.current_projection.z_pos = -1
                            #item.setZValue(new_sub_projection.z_pos)
                            self.update_main_scene(set_position=False)

                            if self.parent_space.current_projection.sub_projections:
                                for subproj in self.parent_space.current_projection.sub_projections:
                                    #print(f"subproj.scaled_projection_pixmap: {subproj.scaled_projection_pixmap}")
                                    subproj.scaled_projection_pixmap.update_path(
                                        self.parent_space.current_projection.scaled_projection_pixmap)
                        break
                else:
                    # пользователь нажал "Отмена" - выходим
                    break
            if not self.parent_space.current_projection:
                self.set_placeholders_on_main_scene()

        except PermissionError as e:
            QMessageBox.warning(self, "Нет прав", str(e))
        except ValueError as e:
            QMessageBox.critical(self, "Ошибка данных", str(e))
        except Exception as e:
            print(f"Unexpected error: {e}")
            QMessageBox.critical(self, "Ошибка", "Произошла непредвиденная ошибка. Обратитесь к администратору.")


    #ACTION
    def add_subspace(self):
        if not self.access_manager.can_edit(self.parent_space):
            QMessageBox.warning(self, "Доступ запрещён",
                                "У вас нет прав для добавления подпространства.")
            return

        add_subspace_dialog = add_space.AddSpace()

        if add_subspace_dialog.exec():
            dict_of_new_space = add_subspace_dialog.get_data()

            new_space = space.Space(dict_of_new_space["name"], dict_of_new_space["description"])
            new_space.mark_new()

            self.parent_space.subspaces.append(new_space)

            if self.parent_space.id_space is not None:
                new_space.id_parent_space = self.parent_space.id_space

            self.add_subspace_projection(new_space)
            self.update_tree_view()
        else:
            return


    # ACTION
    def add_subspace_projection(self, subspace_to_add_projection: space.Space):
        if not self.access_manager.can_edit(subspace_to_add_projection):
            QMessageBox.warning(self, "Доступ запрещён",
                                "У вас нет прав для добавления развертки для этого подпространства.")
            return

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

        add_projection_of_subspace_dialog = add_projection.AddProjection(projection_parent=subspace_to_add_projection)

        while True:
            if add_projection_of_subspace_dialog.exec():
                temp_dict_new_subspace_projection = add_projection_of_subspace_dialog.get_data()

                if self.parent_space.current_projection.projection_width <= temp_dict_new_subspace_projection["x_width"] \
                        or self.parent_space.current_projection.projection_height <= temp_dict_new_subspace_projection["y_height"]:
                    QMessageBox.warning(self, "Подпространство больше пространства",
                                        "Подпространство не может быть больше пространства!")

                else:

                    projection_name = temp_dict_new_subspace_projection["name"]

                    is_projection_name_busy = False
                    if self.parent_space.current_projection.sub_projections:
                        is_projection_name_busy = next((name for name in self.parent_space.current_projection.sub_projections
                                                        if name.projection_name == projection_name), None)
                    if is_projection_name_busy:
                        QMessageBox.warning(self, "Имя занято", "Такое имя уже существует. Пожалуйста, введите другое.")
                        # не очищаем — пользователь увидит свои прежние данные

                    else:
                        original_image = temp_dict_new_subspace_projection["image"]

                        pixmap = utils.get_scaled_pixmap(
                            temp_dict_new_subspace_projection["image"],
                            int(round(self.x_scale * temp_dict_new_subspace_projection["x_width"])),
                            int(round(self.y_scale * temp_dict_new_subspace_projection["y_height"]))
                        )

                        new_sub_projection = pr.Projection(
                            temp_dict_new_subspace_projection["name"],
                            original_image,
                            pixmap,
                            temp_dict_new_subspace_projection["x_width"],
                            temp_dict_new_subspace_projection["y_height"],
                            reference_to_parent_space=subspace_to_add_projection
                        )

                        items = self.scene.items()  # список всех QGraphicsItem
                        if items:
                            max_item = max(items, key=lambda i: i.zValue())
                            max_z_int = int(max_item.zValue())
                            new_sub_projection.z_pos = max_z_int + 1
                        else:
                            new_sub_projection.z_pos = int(0)

                        new_sub_projection.mark_new()

                        # родитель подразвертки это развертка, которая на данный момент отображается как background
                        new_sub_projection.reference_to_parent_projection = self.parent_space.current_projection

                        item = draggable_item.DraggablePixmapItem(pixmap,
                                                                  self,
                                                                  self.parent_space.current_projection.scaled_projection_pixmap,
                                                                  parent=subspace_to_add_projection)

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
                        item.setZValue(new_sub_projection.z_pos)

                        self.scene.addItem(item)
                        self.scene.update_items_movable_flag(item_to_update=item)
                                                                        # при добавлении новой подразвертки
                                                                        # необходимо ей установить флаг возможности её
                                                                        # перемещения в зависимости от прав пользователя

                        break  # успех — выходим из цикла
            else:
                break  # пользователь нажал "Отмена" — выходим


    def is_subprojection_smaller_than_projection(self, projection, width_of_subprojection, height_of_subprojection):
        if (projection.projection_width <= width_of_subprojection
                or projection.projection_height <= height_of_subprojection):
            return False
        else:
            return True


    def change_thing_or_subspace_subprojection(self, draggable):

        # Проверка прав
        if not self.access_manager.can_edit(self.parent_space):
            QMessageBox.warning(self, "Доступ запрещён",
                                "У вас нет прав для редактирования этого пространства.")
            return

        subprojection = self.find_projection(draggable)

        if subprojection is not None:
            projection_parent = subprojection.reference_to_parent_space or subprojection.reference_to_parent_thing
            change_subprojection_dialog = add_projection.AddProjection(projection_parent=projection_parent)
        else:
            return

        # Передаём данные в диалог
        change_subprojection_dialog.name_edit.setText(subprojection.projection_name)
        change_subprojection_dialog.description_edit.setText(subprojection.projection_description)
        change_subprojection_dialog.x_width.setText(str(subprojection.projection_width))
        change_subprojection_dialog.y_height.setText(str(subprojection.projection_height))

        if subprojection.projection_image:
            change_subprojection_dialog.image = subprojection.projection_image
            change_subprojection_dialog.set_image()

        while True:

            if change_subprojection_dialog.exec():
                data = change_subprojection_dialog.get_data()

                print(self.parent_space.current_projection.projection_width)
                print(self.parent_space.current_projection.projection_height)
                print(self.is_subprojection_smaller_than_projection(self.parent_space.current_projection, data["x_width"],
                                                                 data["y_height"]))

                if not self.is_subprojection_smaller_than_projection(self.parent_space.current_projection, data["x_width"],
                                                                 data["y_height"]):
                    QMessageBox.warning(self, "Подпространство больше пространства",
                                        "Подпространство не может быть больше пространства!")

                else:
                        pixmap = utils.get_scaled_pixmap(
                            data["image"],
                            int(round(self.x_scale * data["x_width"])),
                            int(round(self.y_scale * data["y_height"]))
                        )

                        item = draggable_item.DraggablePixmapItem(
                            pixmap,
                            self,
                            self.parent_space.current_projection.scaled_projection_pixmap,
                            parent=subprojection.reference_to_parent_space or subprojection.reference_to_parent_thing
                        )

                        item.update_path()

                        # Если размеры подразвертки увеличились настолько,
                        # что при сохранении тех же координат в системе координат родителя,
                        # подразвертка "вылезет" за пределы развертки-родителя,
                        # то найдем ей новое положение, где она будет помещаться в развертку-родитель
                        # с точнойстью 10 пикселей.
                        # В противном случае оставим подразвертке те же координаты, что были на момент
                        # редактирования

                        if utils.allow_movement(item.path_background, item.path_subprojection, subprojection.x_pos,
                                                subprojection.y_pos):
                            # Обновляем данные subprojection, позиции берется та же, что была
                            subprojection.projection_name = data["name"]
                            subprojection.projection_description = data["description"]
                            subprojection.projection_width = data["x_width"]
                            subprojection.projection_height = data["y_height"]
                            subprojection.projection_image = data["image"]
                            item.setPos(subprojection.x_pos, subprojection.y_pos)
                            subprojection.scaled_projection_pixmap = item
                            self.scene.removeItem(draggable)

                            self.scene.addItem(item)
                            self.scene.update_items_movable_flag()
                            break
                        else:
                            new_position = None
                            for pixel in utils.iterate_pixels_in_path(item.path_background, step=10):
                                if utils.allow_movement(item.path_background, item.path_subprojection, pixel.x(),
                                                        pixel.y()):
                                    new_position = pixel
                                    print(new_position)
                                    break

                            if new_position is None:
                                QMessageBox.warning(self, "Подпространство не помещается",
                                                    "Подпространство не помещается внутри пространства!")
                            else:
                                # Обновляем данные subprojection
                                subprojection.projection_name = data["name"]
                                subprojection.projection_description = data["description"]
                                subprojection.projection_width = data["x_width"]
                                subprojection.projection_height = data["y_height"]
                                subprojection.projection_image = data["image"]
                                subprojection.scaled_projection_pixmap = item
                                item.setPos(new_position)
                                self.scene.removeItem(draggable)

                                self.scene.addItem(item)
                                self.scene.update_items_movable_flag()

                                break
            else:
                break


    def change_thing_information(self, thing_to_change: thing.Thing):

        # Проверка прав
        if not self.access_manager.can_edit(self.parent_space):
            QMessageBox.warning(self, "Доступ запрещён",
                                "У вас нет прав для редактирования этого пространства.")
            return

        try:
            change_thing_dialog = add_thing.AddThing()

            # Заполняем поля текущими данными
            change_thing_dialog.name_edit.setText(thing_to_change.name)
            change_thing_dialog.description_edit.setText(thing_to_change.description)

            # Если есть изображения, добавляем их в диалог
            change_thing_dialog.thing_images = list(thing_to_change.thing_images)  # копия списка
            change_thing_dialog.update_images_layout()

            result = change_thing_dialog.exec()

            if result:
                # Сохраняем изменения обратно в объект
                thing_to_change.name = change_thing_dialog.name_edit.text()
                thing_to_change.description = change_thing_dialog.description_edit.toPlainText()
                thing_to_change.thing_images = list(change_thing_dialog.thing_images)

        except Exception as e:
            print("Ошибка при редактировании вещи:", e)


    def change_space_information(self, space_to_change: space.Space):

        # Проверка прав
        if not self.access_manager.can_edit(space_to_change):
            QMessageBox.warning(self, "Доступ запрещён",
                                "У вас нет прав для редактирования этого подпространства.")
            return

        try:
            change_space_dialog = add_space.AddSpace()

            # Заполняем поля текущими данными
            change_space_dialog.name_edit.setText(space_to_change.name)
            change_space_dialog.description_edit.setText(space_to_change.description)

            result = change_space_dialog.exec()

            if result:
                # Сохраняем изменения обратно в объект
                space_to_change.name = change_space_dialog.name_edit.text()
                space_to_change.description = change_space_dialog.description_edit.toPlainText()

        except Exception as e:
            print("Ошибка при редактировании вещи:", e)


    def add_thing(self):

        if not self.access_manager.can_edit(self.parent_space):
            QMessageBox.warning(
                self,
                "Доступ запрещён",
                "У вас нет прав для добавления вещей."
            )
            return

        add_thing_dialog = add_thing.AddThing()

        while True:
            if add_thing_dialog.exec():
                dict_of_new_space = add_thing_dialog.get_data()

                # if not dict_of_new_space["name"]:
                #     QMessageBox.warning(self, "Заполните обязательные поля",
                #                         "Пожалуйста укажите название вещи!")
                # else:
                new_thing = thing.Thing(dict_of_new_space["name"], self.parent_space)
                new_thing.mark_new()

                if dict_of_new_space["description"]:
                    new_thing.description = dict_of_new_space["description"]

                if dict_of_new_space["thing_images"]:
                    new_thing.thing_images = dict_of_new_space["thing_images"]

                if self.parent_space.id_space is not None:
                    new_thing.id_parent_space = self.parent_space.id_space

                self.parent_space.things.append(new_thing)
                #print(f"self.parent_space.things: {self.parent_space.things}")

                self.add_thing_projection(new_thing)

                self.update_tree_view()

                break  # успех — выходим из цикла

            else:
                break  # пользователь нажал "Отмена" — выходим


    def add_thing_projection(self, thing_to_add_projection: thing.Thing):

        # Проверка прав доступа
        if not self.access_manager.can_edit(self.parent_space):
            QMessageBox.warning(
                self,
                "Доступ запрещён",
                "У вас нет прав для добавления проекции вещи."
            )
            return

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

        add_thing_projection_dialog = add_projection.AddProjection(projection_parent=thing_to_add_projection)

        while True:
            if add_thing_projection_dialog.exec():
                temp_dict_new_thing_projection = add_thing_projection_dialog.get_data()

                original_image = temp_dict_new_thing_projection["image"]

                scaled_pixmap = utils.get_scaled_pixmap(
                    temp_dict_new_thing_projection["image"],
                    int(round(self.x_scale * temp_dict_new_thing_projection["x_width"])),
                    int(round(self.y_scale * temp_dict_new_thing_projection["y_height"])),
                )

                new_thing_projection = pr.Projection(
                    temp_dict_new_thing_projection["name"],
                    original_image,
                    scaled_pixmap,
                    temp_dict_new_thing_projection["x_width"],
                    temp_dict_new_thing_projection["y_height"],
                    # родитель подразвертки это развертка, которая на данный момент отображается как background
                    reference_to_parent_projection=self.parent_space.current_projection,
                    reference_to_parent_thing=thing_to_add_projection
                )

                items = self.scene.items()  # список всех QGraphicsItem
                if items:
                    max_item = max(items, key=lambda i: i.zValue())
                    #print(f"max_item: {max_item}")
                    max_z_int = int(max_item.zValue())
                    new_thing_projection.z_pos = max_z_int + 1
                else:
                    new_thing_projection.z_pos = int(0)

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
                item.setZValue(new_thing_projection.z_pos)
                self.scene.addItem(item)
                self.scene.update_items_movable_flag(item_to_update=item)
                                                        # при добавлении новой подразвертки
                                                        # необходимо ей установить флаг возможности её
                                                        # перемещения в зависимости от прав пользователя

                break  # успех — выходим из цикла

            else:
                break  # пользователь нажал "Отмена" — выходим


    def add_image_of_space(self):

        if not self.access_manager.can_edit(self.parent_space):
            QMessageBox.warning(
                self,
                "Доступ запрещён",
                "У вас нет прав для добавления изображений в это пространство."
            )
            return

        add_image_dialog = add_image.AddImage()

        while True:
            if add_image_dialog.exec():
                image = add_image_dialog.get_data()

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


    def delete_image(self, image):

        if not self.access_manager.can_edit(self.parent_space):
            QMessageBox.warning(
                self,
                "Доступ запрещён",
                "У вас нет прав для удаления изображений."
            )
            return

        if image in self.parent_space.space_images:
            if image.state == ObjectState.NEW:
                self.parent_space.space_images.remove(image)
            else:
                image.mark_deleted()


    def add_new_space_projection(self):

        # Проверка прав доступа
        if not self.access_manager.can_edit(self.parent_space):
            QMessageBox.warning(
                self,
                "Доступ запрещён",
                "У вас нет прав для добавления или замены проекции пространства."
            )
            return

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
                self.save_or_update_mini_projection(self.parent_space.current_projection, check_permissions=False)
                self.parent_space.current_projection = None
                self.add_space_projection()

            elif reply == QMessageBox.StandardButton.No:
                self.scene.clear()
                self.parent_space.current_projection = None
                self.add_space_projection()

            elif reply == QMessageBox.StandardButton.Cancel:
                return


    def save_or_update_mini_projection(self, current_projection, check_permissions=True):

        """
        Сохраняет или обновляет мини-развёртку.

        :param current_projection: Текущая развёртка, которую нужно сохранить/обновить.
        :param check_permissions: Если True, выполняется проверка прав и показывается сообщение.
                                  Если False — выполняется без проверки (для внутренних вызовов).
        """

        # Проверка прав доступа (только если вызов инициирован пользователем)
        if check_permissions:
            if not self.access_manager.can_edit(self.parent_space):
                QMessageBox.warning(
                    self,
                    "Доступ запрещён",
                    "У вас нет прав для сохранения или обновления мини-развёртки."
                )
                return

        if self.placeholder_for_projection_1 and self.placeholder_for_projection_2:
            QMessageBox.warning(self, "Развёртка отсутствует", "У Вас нет развертки для сохранения!")
            return

        if self.parent_space.current_projection:
            if not self.parent_space.current_projection.scaled_projection_pixmap:
                QMessageBox.warning(self, "Развёртка отсутствует", "У Вас нет развертки для сохранения!")
                return
            else:
                self.set_subprojection_position_from_its_scene_position()

                # Если мини проекция уже сохранена, то, если нужно, обновляем её вид
                mini_projection_to_change = next((mini for mini in self.mini_projections_list if
                                                  mini.saved_projection == current_projection), None)
                if mini_projection_to_change:
                    if not self.is_main_scene_equal_to_mini_scene(mini_projection_to_change):
                        mini_projection_to_change.update_scene(current_projection)
                        self.update_mini_projections_layout()

                # Если мини проекция не сохранена, то сохраняем её
                # (также добавляем её в self.parent_space.projections,
                # если она ObjectState.NEW;
                # Если пользователь нажмет "сохранить пространство",
                # то в БД сохранятся те развертки, которые были ранее
                # сохранены, как мини-развертки)
                else:
                    # сохраняем миниразвертки только у разверток, подразвертки не сохраняем как миниразвертки
                    if (
                            # не отображаем подразвёртки на мини проекциях
                            current_projection.reference_to_parent_projection is None
                            and current_projection.id_parent_projection is None
                    ):
                        new_mini_projection = container.ProjectionContainer(
                            current_projection,
                            self#,
                            #self.container_projections_of_space
                        )

                        if self.parent_space.current_projection.state == ObjectState.NEW:
                            self.parent_space.projections.append(self.parent_space.current_projection)
                        #TODO проверить ещё раз
                        self.mini_projections_list.insert(0, new_mini_projection)
                        self.update_mini_projections_layout()


    def delete_mini_projection(self, mini_projection):

        # Проверка прав доступа
        if not self.access_manager.can_edit(self.parent_space):
            QMessageBox.warning(
                self,
                "Доступ запрещён",
                "У вас нет прав для удаления мини-развёртки."
            )
            return

        mini_projection_to_remove = next((mini for mini in self.mini_projections_list if mini == mini_projection),
                                         None)
        if mini_projection_to_remove:
            projection = next((projection for projection in self.parent_space.projections
                               if projection == mini_projection_to_remove.saved_projection), None)

            if projection == self.parent_space.current_projection:
                self.parent_space.current_projection = None
                self.scene.clear()

            if projection:
                # сначала удаляем подразвёртки удаляемой развёртки
                if projection.sub_projections is not None:
                    for sub in projection.sub_projections:
                        if sub.state == ObjectState.NEW:
                            projection.sub_projections.remove(sub)
                        elif sub.state == ObjectState.DELETED:
                            sub.mark_deleted()
                # удаляем саму развёртку
                if projection.state == ObjectState.NEW:
                    self.parent_space.projections.remove(projection)
                else:
                    projection.mark_deleted()


        self.mini_projections_list.remove(mini_projection_to_remove)
        self.update_mini_projections_layout()


    def set_mini_projection_on_main_scene(self, mini_projection):

        """
        Устанавливает выбранную мини-проекцию как активную на главной сцене.

        Функция используется для выбора одной из доступных мини-проекций
        и её отображения на главной сцене приложения.
        """

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


        def get_parent_of_subprojection(draggable):
            if self.parent_space.current_projection.sub_projections:

                subprojection = next((sub for sub in self.parent_space.current_projection.sub_projections
                                                if sub.scaled_projection_pixmap == draggable), None)

                if subprojection:
                    parent_of_subprojection = subprojection.reference_to_parent_space or subprojection.reference_to_parent_thing
                    return parent_of_subprojection
            return None

        if not self.access_manager.can_edit(self.parent_space):
            QMessageBox.warning(
                self,
                "Доступ запрещён",
                "У вас нет прав для удаления подразвертки."
            )
            return
        else:
            parent = get_parent_of_subprojection(draggable_item_pointer)
            if isinstance(parent, space.Space):
                if not self.access_manager.can_edit(parent):
                    QMessageBox.warning(
                        self,
                        "Доступ запрещён",
                        "У вас нет прав для удаления подразвертки этого подпространства."
                    )
                    return

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


                    # мне нужно удалить лишь один draggable. Нет смысла перерисовывать всю сцену.
                    self.scene.removeItem(draggable_item_pointer)
                    # self.set_subprojection_position_from_its_scene_position() # чтобы другие подразвертки не сдвигались,
                    #                                   # изначально у них сохраненная позиция та, что в БД
                    # self.update_main_scene(set_position=True)


    def delete_all_subprojections(self, draggable_item_pointer):

        # Проверка прав доступа
        if not self.access_manager.can_edit(self.parent_space):
            QMessageBox.warning(
                self,
                "Доступ запрещён",
                "У вас нет прав для удаления подразвертки."
            )
            return

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
                                    #!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! --- проверка прав ---
                                    # нельзя удалить подразвертку того пространства, к которому нет доступа
                                    #TODO продумать этот момент
                                    if not self.access_manager.can_edit(subprojection_to_remove.reference_to_parent_space):
                                        continue

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

            # мне нужно удалить лишь один draggable. Нет смысла перерисовывать всю сцену.
            self.scene.removeItem(draggable_item_pointer)

            # self.set_subprojection_position_from_its_scene_position()  # чтобы другие подразвертки не сдвигались,
            # # изначально у них сохраненная позиция та, что в БД
            # self.update_main_scene(set_position=True)
            for proj in self.parent_space.projections:
                self.save_or_update_mini_projection(proj, check_permissions=False)


    # ACTION
    def delete_thing(self, thing_to_delete):

        # Проверка прав доступа
        if not self.access_manager.can_edit(self.parent_space):
            QMessageBox.warning(
                self,
                "Доступ запрещён",
                "У вас нет прав для удаления вещи."
            )
            return

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


    # ACTION
    def delete_subspace(self, subspace_to_delete):

        # Проверка прав доступа
        if not self.access_manager.can_edit(subspace_to_delete):
            QMessageBox.warning(
                self,
                "Доступ запрещён",
                "У вас нет прав для удаления подпространства."
            )
            return

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


    # ACTION
    def delete_space(self):

        # Проверка прав доступа
        if not self.access_manager.can_edit(self.parent_space):
            QMessageBox.warning(
                self,
                "Доступ запрещён",
                "У вас нет прав для удаления пространства."
            )
            return

        if self.parent_space:
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
            #self.set_placeholders_on_main_scene()
            self.save_space_to_DB()


    def save_space_to_DB(self):
        # Проверка прав
        if not self.access_manager.can_edit(self.parent_space):
            QMessageBox.warning(
                self,
                "Доступ запрещён",
                "У вас нет прав для сохранения пространства."
            )
            return

        # Сохраняем текущую мини-развертку, если она ещё не сохранена
        if self.mini_projections_list:
            if not self.is_current_projection_saved():
                reply = QMessageBox.question(
                    self,
                    "Сохранить текущую развертку",
                    "Текущая развертка не сохранена!\nХотите сохранить текущую развертку?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.Yes
                )
                if reply == QMessageBox.StandardButton.Yes:
                    self.save_or_update_mini_projection(self.parent_space.current_projection, check_permissions=False)

        # Фиксируем, какие пространства новые до сохранения
        new_spaces = self._collect_new_spaces(self.parent_space)

        # Сохраняем пространство и все подпространства
        self.parent_space.save_space()

        # Добавляем права editor для всех новых пространств
        self._assign_editor_role_to_new_spaces(new_spaces)

        # Обновляем дерево
        self.show_full_structure_of_space()


    def _collect_new_spaces(self, sp):
        """Рекурсивно собирает все новые пространства (ObjectState.NEW) до сохранения"""
        result = []
        if getattr(sp, "state", None) == ObjectState.NEW:
            result.append(sp)
        for subspace in getattr(sp, "subspaces", []):
            result.extend(self._collect_new_spaces(subspace))
        return result


    def _assign_editor_role_to_new_spaces(self, spaces):
        """Добавляем текущего пользователя как editor для каждого нового пространства"""
        import connect_DB

        config = connect_DB.load_config()
        conn = connect_DB.db_connect(config)
        try:
            with conn:
                with conn.cursor() as cursor:
                    for sp in spaces:
                        cursor.execute(
                            """
                            INSERT INTO spaces.user_access (id_user, id_space, role)
                            VALUES (%s, %s, %s)
                            ON CONFLICT (id_user, id_space) DO NOTHING
                            """,
                            (self.user.id, sp.id_space, "editor")
                        )
        finally:
            conn.close()


    def open_subspace_as_space(self, space_to_open: space.Space):

        # Проверка прав
        if not self.access_manager.can_view(space_to_open):
            QMessageBox.warning(
                self,
                "Доступ запрещён",
                "У вас нет прав для просмотра этого пространства."
            )
            return

        if not self.is_space_saved():
            reply = QMessageBox.question(
                self,
                "Сохранить текущее пространство",
                "Текущее пространство не сохранено!\nХотите сохранить его?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.save_space_to_DB()
            elif reply == QMessageBox.StandardButton.No:
                pass

        if space_to_open.state == ObjectState.NEW:

            self.parent_space = space_to_open
            # если подпространство новое, то у него не может быть еще подразверток
            if self.parent_space.projections:
                self.parent_space.current_projection = random.choice(self.parent_space.projections)

                self.update_main_scene()
                self.update_tree_view()
                self.mini_projections_list.clear()

                for proj in self.parent_space.projections:
                    if (
                            # не отображаем подразвёртки на мини проекциях
                            proj.reference_to_parent_projection is None
                            and proj.id_parent_projection is None
                    ):
                        self.save_or_update_mini_projection(proj, check_permissions=False)
                    self.update_mini_projections_layout()

        elif space_to_open.state == ObjectState.UNMODIFIED:
            self.load_space_from_DB(space_to_open.id_space)

        elif space_to_open.state == ObjectState.MODIFIED:
            reply = QMessageBox.question(self, "Подпространство было изменено",
                                "Вы изменили это пространство, но эти "
                                "изменения ещё не были сохранены. "
                                "Хотите сохранить эти изменения?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )

            if reply == QMessageBox.StandardButton.Yes:
                space_to_open.save_space()
                self.load_space_from_DB(space_to_open.id_space)
            elif reply == QMessageBox.StandardButton.No:
                self.load_space_from_DB(space_to_open.id_space)

        self.update_tree_view()
        self.update_main_scene()
        self.fill_mini_projections_list(self.parent_space.projections)
        for proj in self.parent_space.projections:
            self.save_or_update_mini_projection(proj, check_permissions=False)
        self.update_images_layout()


    def fill_mini_projections_list(self, space_projections: list):
        self.mini_projections_list.clear()
        for proj in space_projections:
            if proj.state != ObjectState.DELETED:
                new_mini_projection = container.ProjectionContainer(
                    proj,
                    self#,
                    #self.container_projections_of_space
                )
                print(f"new: {new_mini_projection}")
                self.mini_projections_list.append(new_mini_projection)





    def load_space_from_DB(self, id_space, thing_to_show=None):
        try:
            loaded_space = space.load_space_by_id(id_space)
            # Проверка прав
            if loaded_space is not None:
                if not self.access_manager.can_view(loaded_space):
                    return

            self.parent_space = loaded_space

            if self.current_index == 0:
                self.current_index = 1
                self.stack_widget.setCurrentIndex(self.current_index)

            if self.mini_projections_list:
                self.mini_projections_list.clear()
                self.update_mini_projections_layout()

            self.update_tree_view()
            self.update_images_layout()

            if not self.parent_space.projections:
                self.update_main_scene()

            else:

                for proj in self.parent_space.projections:
                    for subproj in proj.sub_projections:

                        if subproj.id_parent_thing:
                            subproj.reference_to_parent_thing = (
                                next((thing_item for thing_item in self.parent_space.things
                                      if thing_item.id_thing == subproj.id_parent_thing), None))

                        elif subproj.id_parent_space:
                            subproj.reference_to_parent_space = next(
                                (space_item for space_item in self.parent_space.subspaces
                                 if space_item.id_space == subproj.id_parent_space), None)

                if thing_to_show is not None:
                    for proj in self.parent_space.projections:
                        if proj.sub_projections:
                            subprojection = next(
                                (
                                    subprojection
                                    for subprojection in proj.sub_projections
                                    if getattr(subprojection.reference_to_parent_thing, "id_thing",
                                               None) == thing_to_show.id_thing
                                ),
                                None
                            )

                            if subprojection is not None:
                                #print(f"subprojection: {subprojection}")
                                self.parent_space.current_projection = proj
                                break
                else:
                    # выбираем как главную развёртку ту, у которой самое большое количество подразверток или,
                    # если подразвёрток ни у одной развертки нет, то первую в списке projections
                    self.parent_space.current_projection = max(self.parent_space.projections,
                                                               key=lambda p: len(p.sub_projections))

                self.x_scale = (self.parent_space.current_projection.original_pixmap.width()
                                / self.parent_space.current_projection.projection_width)
                self.y_scale = (self.parent_space.current_projection.original_pixmap.height()
                                / self.parent_space.current_projection.projection_height)

                self.update_main_scene(True)

                for proj in self.parent_space.projections:
                    self.save_or_update_mini_projection(proj, check_permissions=False)

                if thing_to_show is not None:
                    self.highlight_subprojections_on_mini_projections(thing_to_highlight=thing_to_show)

            self.space_changed.emit()
            self.set_buttons_disabled_or_enabled()

            if thing_to_show is not None:
                self.handle_node_clicked(thing_to_show)

        except Exception as e:
            print(e)


    def load_parent_space_from_DB(self):
        if not self.parent_space.id_parent_space:
            QMessageBox.warning(
                self,
                "Родительское пространство отсутствует",
                "Для этого пространства нет родительского пространства!"
            )
            return
        else:
            # Проверка прав
            if not self.access_manager.can_view(self.parent_space.id_parent_space):
                #print(f"-----ID: {self.parent_space.id_parent_space}")
                #print(f"-----USER-ID: {self.user.id}")
                QMessageBox.warning(
                    self,
                    "Доступ запрещён",
                    "У вас нет прав для просмотра родительского пространства."
                )
                return

        self.load_space_from_DB(self.parent_space.id_parent_space)


    def load_space_from_db_by_selection_from_spaces_list(self):
        spaces_in_DB = all_spaces_in_DB.load_all_spaces_from_DB(self.user.id, self.user.role)

        if spaces_in_DB is None:
            QMessageBox.warning(self, "Нет пространств", "В базе данных пока нет ни одного пространства!")
            return

        spaces_list = all_spaces_in_DB.SpacesList(spaces_in_DB)

        def on_selected(row):
            print(f"Выбранная строка: {row}")

            if self.mini_projections_list:
                self.mini_projections_list.clear()
                self.update_mini_projections_layout()

            # получаю id_space выбранного пространства
            id_space = spaces_in_DB[row][0]

            self.load_space_from_DB(id_space)

        spaces_list.spaceDoubleClicked.connect(on_selected)

        if spaces_list.exec():
            print("Диалог закрыт с accept")
        else:
            print("Диалог закрыт без выбора")


    def show_full_structure_of_space(self):

        """
        Отображает полную иерархическую структуру текущего пространства.

        Функция проверяет, является ли текущее пространство новым.
        Если пространство уже существует (не имеет состояния NEW),
        определяется верхний уровень иерархии (топ-пространство),
        начиная с которого загружается полная структура.
        Затем дерево структуры обновляется и отображается в соответствующем элементе интерфейса.

        Если же текущее пространство новое, пользователю выводится предупреждающее сообщение о том,
        что структура уже полностью показана в дереве справа.
        """

        if self.parent_space.state != ObjectState.NEW:

            if self.parent_space.id_parent_space:
                id_top_space = space.get_top_space_id(self.parent_space.id_parent_space)
            else:
                id_top_space = self.parent_space.id_space

            top_space = space.load_space_by_id(id_top_space)

            self.tree_view_of_full_space_structure.update_tree(top_space)
            self.tree_view_of_full_space_structure.show()

        else:
            QMessageBox.warning(self, "Новое пространство", "Это пространство новое, его структура "
                                                            "уже показана полностью в дереве справа!")


    def show_thing_information(self, thing_to_show_information):
        from information_about_thing import ThingInformation
        thing_info = ThingInformation(thing_to_show_information)
        thing_info.show()

        self.information_about_things.append(thing_info)


    def show_space_information(self, space_to_show_information):
        from information_about_space import SpaceInformation
        space_info = SpaceInformation(space_to_show_information)
        space_info.show()

        self.information_about_spaces.append(space_info)


    def show_all_things_in_space(self, sp: space.Space):
        from information_about_thing import ThingInformation

        if not sp.things:
            QMessageBox.information(
                self,
                f"Пространство {sp.name}",
                "В этом пространстве ещё нет вещей!"
            )
            return

        scroll_window = QScrollArea()
        scroll_window.setWindowTitle(f"Все вещи в пространстве {sp.name}")
        scroll_window.setWindowIcon(QIcon("icons/mini_logo.png"))
        scroll_window.setWidgetResizable(True)

        # Контейнер для виджетов информации о вещах
        things_info = QWidget()
        layout = QVBoxLayout(things_info)

        for th in sp.things:
            #print(th.name)
            info = ThingInformation(th)
            layout.addWidget(info)

        things_info.setLayout(layout)
        scroll_window.setWidget(things_info)
        #scroll_window.resize(600, 400)

        # ссылка, чтобы окно не удалилось сборщиком мусора
        if not hasattr(self, "_open_space_windows"):
            self._open_space_windows = []
        self._open_space_windows.append(scroll_window)

        scroll_window.show()


    def find_projection(self, draggable_on_scene):
        if self.parent_space:
            if self.parent_space.current_projection:
                if self.parent_space.current_projection.sub_projections:
                    projection = next((proj for proj in self.parent_space.current_projection.sub_projections
                                       if proj.scaled_projection_pixmap == draggable_on_scene), None)

                    if projection:
                        #print(f"----projection: {projection}")
                        return projection
        return None


    def move_draggable_to_another_z_position(self, draggable_to_move, parent_name_of_reference_subprojection):
        """
        Перемещает элемент (`draggable_to_move`) на новый уровень по оси Z относительно другого элемента на сцене.
        """

        # Проверка прав
        if not self.access_manager.can_view(self.parent_space):
            QMessageBox.warning(
                self,
                "Доступ запрещён",
                "У вас нет прав для редактирования пространства."
            )
            return

        # Находим перемещаемый subprojection
        subprojection_to_move = next(
            (sub for sub in self.parent_space.current_projection.sub_projections
             if sub.scaled_projection_pixmap == draggable_to_move),
            None
        )

        # Находим reference_subprojection по имени связанного родителя
        reference_subprojection = next(
            (sub for sub in self.parent_space.current_projection.sub_projections
             if ((sub.reference_to_parent_space is not None and
                  sub.reference_to_parent_space.name == parent_name_of_reference_subprojection)
                 or
                 (sub.reference_to_parent_thing is not None and
                  sub.reference_to_parent_thing.name == parent_name_of_reference_subprojection))),
            None
        )

        if not subprojection_to_move or not reference_subprojection:
            print("Ошибка: один из подэлементов не найден.")
            return

        if not (self.parent_space and self.parent_space.current_projection and
                self.parent_space.current_projection.sub_projections):
            print("Ошибка: текущая проекция или список подэлементов отсутствует.")
            return

        # Сортируем по текущему z_pos
        self.parent_space.current_projection.sub_projections.sort(
            key=lambda sub: sub.z_pos
        )

        try:
            index_1 = self.parent_space.current_projection.sub_projections.index(subprojection_to_move)
            index_2 = self.parent_space.current_projection.sub_projections.index(reference_subprojection)
        except ValueError:
            print("Ошибка: элементы не найдены в отсортированном списке.")
            return

        if index_1 == index_2:
            # чтобы зря не перерисовывать сцену
            return

        if index_1 < index_2:
            subprojection_to_move.z_pos = reference_subprojection.z_pos
            for subprojection in self.parent_space.current_projection.sub_projections[index_1 + 1 : index_2 + 1]:
                subprojection.z_pos -= 1.0

        else: # index_2 < index_1
            subprojection_to_move.z_pos = reference_subprojection.z_pos + 1
            for subprojection in self.parent_space.current_projection.sub_projections[index_2 + 1 : index_1]:
                subprojection.z_pos += 1.0

        for sub in self.parent_space.current_projection.sub_projections:
            print(f"{sub.projection_name}: {sub.z_pos}")

        self.set_subprojection_position_from_its_scene_position(z=False) # z не надо брать со сцены,
                                                                         # потому что мы именно её сейчас рассчитываем
                                                                         # и устанавливаем для правильной отрисовки на сцене
        self.update_main_scene(set_position=True)


    ################################################################################################################

    def set_buttons_disabled_or_enabled(self):
        if self.parent_space is None or self.parent_space.state == ObjectState.DELETED:
            self.add_image_of_space_button.setEnabled(False)
            self.add_new_space_projection_button.setEnabled(False)
            self.save_current_projection_button.setEnabled(False)
        else:
            self.add_image_of_space_button.setEnabled(True)
            self.add_new_space_projection_button.setEnabled(True)
            self.save_current_projection_button.setEnabled(True)


    def highlight_subprojections_on_mini_projections(self, parent=None, thing_to_highlight=None):
        for mini_projection in self.mini_projections_list:
            # Всегда очищаем старые выделения
            mini_projection.clear_highlights()

            subprojection_to_highlight = None

            if thing_to_highlight is not None:
                #print("thing_to_highlight is not None")
                subprojection_to_highlight = next(
                    (item for item in mini_projection.scene.items()
                     if isinstance(item, QGraphicsPixmapItem)
                     and getattr(item, "thing_id", None) == thing_to_highlight.id_thing),
                    None
                )

            if parent is not None:
                # Ищем item, чей .parent соответствует переданному parent
                subprojection_to_highlight = next(
                    (item for item in mini_projection.scene.items()
                     if isinstance(item, QGraphicsPixmapItem) and getattr(item, "parent", None) == parent),
                    None
                )

            if subprojection_to_highlight:
                mini_projection.highlight(subprojection_to_highlight)


    def set_subprojection_position_from_its_scene_position(self, x=True, y=True, z=True):
        if self.parent_space.current_projection.sub_projections:
            for sub_projection in self.parent_space.current_projection.sub_projections:
                if sub_projection.state != ObjectState.DELETED:
                    item = sub_projection.scaled_projection_pixmap
                    if item is None or self.parent_space.current_projection.scaled_projection_pixmap is None:
                        continue
                    relative_pos = self.parent_space.current_projection.scaled_projection_pixmap.mapFromItem(item,
                                                                                                             0, 0)
                    if x:
                        sub_projection.x_pos = relative_pos.x()
                    if y:
                        sub_projection.y_pos = relative_pos.y()
                    if z:
                        sub_projection.z_pos = item.zValue()


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
        # чтобы миниразвертки прижимались к верхнему краю
        self.layout_projections_of_space.setAlignment(Qt.AlignmentFlag.AlignTop)


    def is_current_projection_saved(self):
        if self.placeholder_for_projection_1 is not None and self.placeholder_for_projection_2 is not None:
            return True
        else:
            mini_projection = next((mini for mini in self.mini_projections_list
                             if mini.saved_projection == self.parent_space.current_projection), None)
            if mini_projection:
                is_main_scene_equal_to_mini_scene = self.is_main_scene_equal_to_mini_scene(mini_projection)
                return is_main_scene_equal_to_mini_scene
            else:
                return False


    def is_main_scene_equal_to_mini_scene(self, mini):
        def sort_key(item):
            return item.zValue(), item.pos().x(), item.pos().y()

        items_main = sorted(self.scene.items(), key=sort_key)
        items_mini = sorted(mini.scene.items(), key=sort_key)

        if len(items_main) != len(items_mini):
            #print("len не равны")
            return False

        for item_main, item_mini in zip(items_main, items_mini):
            # QGraphicsPixmapItem и DraggablePixmapItem в данном случае будут сравниваться, как равные
            if not isinstance(item_main, QGraphicsPixmapItem) or not isinstance(item_mini, QGraphicsPixmapItem):
                #print("типы не равны")
                return False

            if item_main.pos() != item_mini.pos():
                #print("позиции не равны")
                return False

            if item_main.zValue() != item_mini.zValue():
                #print("Z не равны")
                return False

        return True


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


    def set_x_and_y_scales(self, scaled_cropped_pixmap, real_projection_width, real_projection_height):
        self.x_scale = scaled_cropped_pixmap.width() / real_projection_width
        self.y_scale = scaled_cropped_pixmap.height() / real_projection_height


    def update_main_scene(self, set_position=None):
        try:
            if self.scene.items():
                self.scene.clear()
                self.placeholder_for_projection_1 = None
                self.placeholder_for_projection_2 = None

            if self.parent_space.current_projection is not None:
                self.parent_space.current_projection.scaled_projection_pixmap \
                    = QGraphicsPixmapItem(self.parent_space.current_projection.original_pixmap)
                min_z = min((item.zValue() for item in self.scene.items()), default=0)
                self.parent_space.current_projection.scaled_projection_pixmap.setZValue(min_z - 1)  # Отправляем фон на самый задний план
                self.parent_space.current_projection.scaled_projection_pixmap.setTransformationMode(Qt.TransformationMode.SmoothTransformation)
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
                            if sub.z_pos is not None:
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

                # в зависимости от прав пользователя можно или нет двигать развертки подпространств и вещей
                if self.scene.items():
                    self.scene.update_items_movable_flag()


            else:
                self.set_placeholders_on_main_scene()

        except Exception as e:
            print(f"Ошибка в update_main_scene: {e}")
            import traceback
            traceback.print_exc()


    def handle_node_clicked(self,
                            clicked_ref):
        try:
            # Удаляем эффект подсветки
            for item in self.scene.items():
                if isinstance(item, QGraphicsPixmapItem):
                    item.setGraphicsEffect(None)

            def focus_and_highlight(target_item):
                # Устанавливаем фокус и подсветку на выбранный
                #target_item.setFlag(QGraphicsPixmapItem.GraphicsItemFlag.ItemIsFocusable)
                self.view.setFocus()
                target_item.setFocus()

                effect = QGraphicsDropShadowEffect()
                effect.setBlurRadius(15)
                effect.setColor(QColor("red"))
                effect.setOffset(0, 0)
                target_item.setGraphicsEffect(effect)

            #draggable_pixmap_item = None
            if self.parent_space.current_projection:
                if self.parent_space.current_projection.sub_projections:

                    item_on_scene = None

                    if isinstance(clicked_ref, thing.Thing):

                        if clicked_ref.id_thing is not None:
                            subprojection = next(
                                (
                                    subprojection
                                    for subprojection in self.parent_space.current_projection.sub_projections
                                    if getattr(subprojection.reference_to_parent_thing, "id_thing",
                                               None) == clicked_ref.id_thing
                                ),
                                None
                            )
                        else:
                            subprojection = next((subprojection for subprojection
                                                         in self.parent_space.current_projection.sub_projections
                                                         if subprojection.reference_to_parent_thing == clicked_ref), None)

                        if subprojection:
                            item_on_scene = next((draggable_pixmap_item for draggable_pixmap_item in self.scene.items()
                                                  if draggable_pixmap_item == subprojection.scaled_projection_pixmap), None)
                            #print(f"ITEM ON SCENE: {item_on_scene}")

                            #focus_and_highlight(item_on_scene)

                    else:
                        subprojection = next((subprojection for subprojection
                                                     in self.parent_space.current_projection.sub_projections
                                                     if subprojection.reference_to_parent_space == clicked_ref), None)


                        if subprojection:
                            item_on_scene = next((draggable_pixmap_item for draggable_pixmap_item in self.scene.items()
                                                  if draggable_pixmap_item == subprojection.scaled_projection_pixmap), None)
                            #print(f"ITEM ON SCENE: {item_on_scene}")

                    if item_on_scene:
                        focus_and_highlight(item_on_scene)
        except Exception as e:
            print(e)


    def update_scene_size(self):
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)


    def update_placeholder_of_wellcome_view(self):
        self.wellcome_view.fitInView(self.wellcome_scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)


    def set_placeholders_on_main_scene(self):
        self.placeholder_for_projection_1 = QGraphicsTextItem(
            "Добавьте сюда проекцию пространства, кликнув правой кнопкой мыши на"
        )
        self.placeholder_for_projection_2 = QGraphicsTextItem(
            "пространстве в списке справа, или нажав на кнопку \"Добавить новую проекцию пространства\"."
        )

        self.placeholder_for_projection_1.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        self.placeholder_for_projection_2.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)

        self.scene.addItem(self.placeholder_for_projection_1)
        self.scene.addItem(self.placeholder_for_projection_2)

        self.update_placeholders_font_and_position()


    def update_placeholders_font_and_position(self):
        if not self.placeholder_for_projection_1 or not self.placeholder_for_projection_2:
            return

        vw = self.view.viewport()
        w = vw.width()
        h = vw.height()

        if w <= 0 or h <= 0:
            return

        font_size = max(int(min(w, h) * 0.035), 5)
        font = QFont("Arial", font_size)

        self.placeholder_for_projection_1.setFont(font)
        self.placeholder_for_projection_2.setFont(font)

        r1 = self.placeholder_for_projection_1.boundingRect()
        r2 = self.placeholder_for_projection_2.boundingRect()

        total_height = r1.height() + r2.height()
        y1 = (h - total_height) / 2
        x1 = (w - r1.width()) / 2
        x2 = (w - r2.width()) / 2
        y2 = y1 + r1.height()

        self.placeholder_for_projection_1.setPos(x1, y1)
        self.placeholder_for_projection_2.setPos(x2, y2)

        self.scene.setSceneRect(self.scene.itemsBoundingRect())
        self.view.fitInView(self.scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)


    def update_tree_view(self):
        self.tree.update_tree(self.parent_space)


    def update_app_view(self):
        self.update_main_scene()
        self.mini_projections_list.clear()
        self.update_mini_projections_layout()
        self.update_tree_view()
        #if self.parent_space.space_images:
        self.update_images_layout()


    def show_space_of_thing(self, space_id, highlight_name):
        try:

            #id_top_space = space.get_top_space_id(space_id)
            top_space = space.load_space_by_id(space_id)
            tree_view_for_thing = tree_view_for_search.TreeWidgetForSearch(self)

            #print(f"позиция: {self.pos().x() + self.offset_for_found_things_trees}, {self.pos().y() + self.offset_for_found_things_trees}")

            tree_view_for_thing.move(self.mapToGlobal(self.rect().topLeft())
                                     + QPoint(self.offset_for_found_things_trees, self.offset_for_found_things_trees))
            self.offset_for_found_things_trees += 30

            tree_view_for_thing.update_tree(top_space, highlight_name=highlight_name)
            tree_view_for_thing.show()

            self.found_things_tree_views.append(tree_view_for_thing)
            return top_space

        except Exception as e:
            print(f"Ошибка в find_top_space_of_thing: {e}")


    def is_space_saved(self):
        if self.parent_space:
            if not self.is_current_projection_saved():
                return False


            if (self.parent_space.state == ObjectState.NEW
                    or self.parent_space.state == ObjectState.MODIFIED
                    or self.parent_space.state == ObjectState.DELETED):
                return False

            else:
                if self.parent_space.things:
                    for th in self.parent_space.things:
                        if (th.state == ObjectState.NEW
                                or th.state == ObjectState.MODIFIED
                                or th.state == ObjectState.DELETED):
                            return False

                if self.parent_space.space_images:
                    for img in self.parent_space.space_images:
                        if (img.state == ObjectState.NEW
                                or img.state == ObjectState.MODIFIED
                                or img.state == ObjectState.DELETED):
                            return False

                if self.parent_space.projections:
                    for proj in self.parent_space.projections:
                        if (proj.state == ObjectState.NEW
                                or proj.state == ObjectState.MODIFIED
                                or proj.state == ObjectState.DELETED):
                            return False
                        if proj.sub_projections:
                            for pr in proj.sub_projections:
                                if (pr.state == ObjectState.NEW
                                        or pr.state == ObjectState.MODIFIED
                                        or pr.state == ObjectState.DELETED):
                                    return False

                if self.parent_space.subspaces:
                    for sub in self.parent_space.subspaces:
                        if (sub.state == ObjectState.NEW
                                or sub.state == ObjectState.MODIFIED
                                or sub.state == ObjectState.DELETED):
                            return False

                return True
        else:
            return True


def main():
    app = QApplication(sys.argv)
    login_dialog = log.LogIn()

    if login_dialog.exec() != QDialog.DialogCode.Accepted:
        sys.exit()

    user = login_dialog.get_user()
    if user is None:
        sys.exit()

    main_window = MainWindow(user)
    main_window.show()
    sys.exit(app.exec())



if __name__ == "__main__":
    main()