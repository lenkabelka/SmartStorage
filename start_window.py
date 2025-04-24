import sys
from PyQt6.QtWidgets import QApplication, QFrame, QWidget, QStackedLayout, QVBoxLayout, QPushButton, QLabel, QMenuBar, \
    QMenu, QHBoxLayout, QGridLayout, QGraphicsView, QGraphicsScene
from PyQt6.QtGui import QAction, QPixmap, QPainter
from PyQt6.QtCore import QSize, Qt, QRectF
from PyQt6.QtGui import QAction, QIcon, QGuiApplication
from PyQt6.QtWidgets import (
    QApplication,
    QSizePolicy,
    QCheckBox,
    QLabel,
    QMainWindow,
    QStatusBar,
    QToolBar,
)

import space as space

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("My App")

        button_style = """
            QPushButton {
                background-color: grey;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 40px;
            }
            QPushButton:hover {
                background-color: grey;
            }
            QPushButton:pressed {
                background-color: darkgrey;
            }
        """

        label_style = """
            QLabel {
                background-color: grey;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 40px;
            }
        """

        self.start_window = QWidget(self)
        self.create_change_space = QWidget(self)
        self.search_item_mode = QWidget(self)

        self.stacked_layout = QStackedLayout()
        self.stacked_layout.addWidget(self.start_window)
        self.stacked_layout.addWidget(self.create_change_space)
        self.stacked_layout.addWidget(self.search_item_mode)

        #self.central_widget = QWidget(self)

        screen = QGuiApplication.primaryScreen()
        size = screen.availableGeometry()

        self.resize(size.width(), int(size.height()*0.97))
        self.setCentralWidget(self.start_window)

        size_policy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)

        self.main_layout = QVBoxLayout(self)
        #main_layout.setSpacing(4)
        #main_layout.setContentsMargins(0, 0, 0, 0)


        self.wellcome_label = QLabel("Wellcome to the application SmartStorage!")
        self.wellcome_label.setStyleSheet(label_style)
        self.wellcome_label.setSizePolicy(size_policy)
        self.main_layout.addWidget(self.wellcome_label)
        self.main_layout.setAlignment(self.wellcome_label, Qt.AlignmentFlag.AlignCenter)

        self.create_new_space = QPushButton("Create new space")
        self.create_new_space.setStyleSheet(button_style)

        self.open_space = QPushButton("Open saved space")
        self.open_space.setStyleSheet(button_style)

        self.main_layout.addWidget(self.create_new_space)
        self.main_layout.addWidget(self.open_space)

        self.create_new_space.setSizePolicy(size_policy)
        self.main_layout.setAlignment(self.create_new_space, Qt.AlignmentFlag.AlignCenter)
        self.open_space.setSizePolicy(size_policy)
        self.main_layout.setAlignment(self.open_space, Qt.AlignmentFlag.AlignCenter)

        self.start_window.setLayout(self.main_layout)


        #label = QLabel("Hello!")
        #label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        menu = self.menuBar()

        button_action = QAction("&Your button", self)
        button_action.setStatusTip("This is your button")
        button_action.triggered.connect(self.toolbar_button_clicked)
        #button_action.setCheckable(True)

        button_action_1 = QAction("&Your button_1", self)
        button_action_1.triggered.connect(self.toolbar_button_clicked_1)

        button_action_2 = QAction("&About application", self)
        button_action_1.triggered.connect(self.toolbar_button_clicked_1)

        file_menu = menu.addMenu("&Menu")
        file_menu.addAction(button_action)
        file_menu.addAction(button_action_1)

        about_menu = menu.addMenu("&About")
        about_menu.addAction(button_action_2)

        #horizontal_layout = QHBoxLayout(central_widget)
        #horizontal_layout.addLayout(main_layout)

        self.stacked_layout.setCurrentIndex(0)
        #self.setLayout(self.stacked_layout)

        #layout = QVBoxLayout()
        #widget = QWidget()
        #layout.addWidget(widget)
        #self.start_window.setLayout(layout)


#################### View: create/change space ##########################################################################
        #self.setCentralWidget(self.create_change_space)
        self.scene = QGraphicsScene()

        self.pixmap = QPixmap("circle.png")
        self.polygon_item = space.ClickablePolygon()
        self.pixmap_item = space.ImageWithPolygon(self.pixmap, self.polygon_item)

        self.scene.addItem(self.pixmap_item)
        self.scene.addItem(self.polygon_item)
        self.scene.setSceneRect(QRectF(self.pixmap.rect()))

        #self.create_change_space.resize(self.pixmap.rect().width(), self.pixmap.rect().height())

        self.view = QGraphicsView(self.scene)

        def finish_on_key(event):
            if event.key() == Qt.Key.Key_Return:
                self.polygon_item.finish_polygon()

        self.view.keyPressEvent = finish_on_key
        self.view.setScene(self.scene)
        self.view.setMinimumSize(self.pixmap.rect().width(), self.pixmap.rect().height())


        #self.window_create_change_space = QWidget(self)
        self.layout_create_change_space = QVBoxLayout()
        self.create_change_space.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)


        #self.scene= QGraphicsScene()
        #self.space_image = space.ClickablePolygon()
        #self.scene.addItem(self.space_image)

        #self.view = QGraphicsView(self.scene)

        self.layout_for_image = QVBoxLayout()
        self.layout_for_image.addWidget(self.view)


        #self.layout_create_change_space.addWidget(self.add_space)

        #self.container_widget = QWidget(self)
        #self.container_widget.setLayout(self.layout_create_change_space)

        self.layout_for_buttons = QHBoxLayout()

        self.add_subspace = QPushButton("Add subspace")
        self.add_subspace.setStyleSheet(button_style)

        self.add_item = QPushButton("Add item in space")
        self.add_item.setStyleSheet(button_style)

        self.add_item_into_subspace = QPushButton("Add item in subspace")
        self.add_item_into_subspace.setStyleSheet(button_style)

        self.layout_for_buttons.addWidget(self.add_subspace)
        self.layout_for_buttons.addWidget(self.add_item)
        self.layout_for_buttons.addWidget(self.add_item_into_subspace)

        self.layout_create_change_space.addLayout(self.layout_for_image)
        self.layout_create_change_space.addLayout(self.layout_for_buttons)

        self.create_change_space.setLayout(self.layout_create_change_space)
############################

        self.create_new_space.clicked.connect(self.create_new_space_clicked)
        #!!!!!!!!!!! self.add_subspace.clicked.connect(lambda e: self.polygon_item.mousePressEvent(event=e))


    def toolbar_button_clicked(self):
        print("click")

    def toolbar_button_clicked_1(self):
        print("click_1")

    def create_new_space_clicked(self):
        #pass
        self.setCentralWidget(self.create_change_space)
        self.stacked_layout.setCurrentIndex(1)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())