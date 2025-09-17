from PyQt6.QtWidgets import QTreeView, QMenu, QApplication
from PyQt6.QtCore import (
    Qt, QAbstractItemModel, QModelIndex, QPoint
)
from PyQt6.QtGui import QIcon, QPalette, QColor
from track_object_state import ObjectState
import sys
import space
import connect_DB

NODE_TYPE_SPACE = "space"
NODE_TYPE_THING = "thing"


class TreeNode:
    def __init__(self, ref, name, node_type, parent=None):
        self.ref = ref
        self.name = name
        self.node_type = node_type
        self.parent = parent
        self.children = []

    def add_child(self, child):
        self.children.append(child)
        child.thing_or_space_parent = self

    def child_count(self):
        return len(self.children)

    def child(self, row):
        return self.children[row]

    def row(self):
        if self.parent:
            return self.parent.children.index(self)
        return 0


class TreeModel(QAbstractItemModel):
    def __init__(self, root_item, app_widget, highlight_name=None):
        super().__init__()
        self.root_item = root_item
        self.app_ref = app_widget
        self.highlight_name = highlight_name

    def get_item(self, index: QModelIndex):
        if index.isValid():
            return index.internalPointer()
        return self.root_item

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return self.get_item(parent).child_count()

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 1

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        parent_item = self.get_item(parent)
        if row < 0 or row >= parent_item.child_count():
            return QModelIndex()
        child_item = parent_item.child(row)
        return self.createIndex(row, column, child_item)

    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()
        item = index.internalPointer()
        parent_item = item.thing_or_space_parent
        if parent_item is None or parent_item == self.root_item:
            return QModelIndex()
        return self.createIndex(parent_item.row(), 0, parent_item)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None

        item = index.internalPointer()

        if role == Qt.ItemDataRole.DisplayRole:
            return item.name

        elif role == Qt.ItemDataRole.DecorationRole:
            if item.node_type == NODE_TYPE_SPACE:
                return QIcon("icons/space.png")  # путь к иконке пространства
            elif item.node_type == NODE_TYPE_THING:
                return QIcon("icons/thing_1.jpg")   # путь к иконке вещи

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return "Структура пространства"
        return None


class TreeWidgetForSearch(QTreeView):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Дерево пространства")
        self.setWindowIcon(QIcon("icons/mini_logo.png"))
        self.root_item = TreeNode(None,"root", NODE_TYPE_SPACE)
        self.model = TreeModel(self.root_item, self)
        self.setModel(self.model)

        self.app_ref = app

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)

        # Настройка выделения через стиль
        self.setStyleSheet("""
            QTreeView::item:selected {
                background-color: rgb(200, 230, 255); /* нежно-зелёный */
                color: black;                         /* чёрный текст */
            }
        """)

    def build_tree_nodes(self, space_in_DB):
        current_node = TreeNode(space_in_DB, space_in_DB.name, NODE_TYPE_SPACE)

        # Рекурсивно обрабатываем подпространства
        for subspace in getattr(space_in_DB, "subspaces", []):
            child_node = self.build_tree_nodes(subspace)  # РЕКУРСИЯ ЗДЕСЬ
            current_node.add_child(child_node)

        # Обрабатываем вещи
        for thing in getattr(space_in_DB, "things", []):
            thing_node = TreeNode(thing, thing.name, NODE_TYPE_THING)
            current_node.add_child(thing_node)

        return current_node


    # def update_tree(self, space_in_DB=None):
    #     """Обновляет модель, начиная с нового пространства"""
    #     # Новый root (невидимый)
    #     self.root_item = TreeNode(None, "root", NODE_TYPE_SPACE)
    #
    #     if space_in_DB is not None:
    #         root_child = self.build_tree_nodes(space_in_DB)
    #         if root_child is not None:
    #             self.root_item.add_child(root_child)
    #         else:
    #             print("Корневое пространство удалено. Показывается только скрытый root.")
    #
    #     self.model = TreeModel(self.root_item, self)
    #     self.setModel(self.model)
    #     self.expandAll()

    def update_tree(self, space_in_DB=None, highlight_name: str = None):
        """Обновляет модель, начиная с нового пространства, и подсвечивает указанную вещь"""
        # Новый root (невидимый)
        self.root_item = TreeNode(None, "root", NODE_TYPE_SPACE)

        if space_in_DB is not None:
            root_child = self.build_tree_nodes(space_in_DB)
            if root_child is not None:
                self.root_item.add_child(root_child)
            else:
                print("Корневое пространство удалено. Показывается только скрытый root.")

        self.model = TreeModel(self.root_item, self)
        self.setModel(self.model)
        self.expandAll()

        # Подсветка (если задано имя)
        if highlight_name:
            index = self.find_index_by_name(highlight_name)
            if index.isValid():
                self.setCurrentIndex(index)
                self.scrollTo(index)  # прокрутить к элементу

    def find_index_by_name(self, name: str):
        """Ищет индекс по имени вещи"""

        def recursive_search(parent_index):
            rows = self.model.rowCount(parent_index)
            for row in range(rows):
                index = self.model.index(row, 0, parent_index)
                if index.isValid():
                    item_name = index.data()  # предполагаю, что data() возвращает имя
                    if item_name == name:
                        return index
                    # рекурсивно спускаемся вниз
                    result = recursive_search(index)
                    if result.isValid():
                        return result
            return QModelIndex()

        return recursive_search(QModelIndex())


    def open_context_menu(self, position: QPoint):
        index = self.indexAt(position)
        if not index.isValid():
            return

        item = index.internalPointer()
        node_type = item.node_type

        menu = QMenu(self)

        if node_type == NODE_TYPE_SPACE:
            menu.addAction("Открыть пространство для редактирования",
                           lambda: self.app_ref.load_space_from_DB(index.internalPointer().ref.id_space))

            menu.addAction("Посмотреть информацию о пространстве",
                           lambda: self.app_ref.show_space_information(index.internalPointer().ref))

        elif node_type == NODE_TYPE_THING:
            menu.addAction("Посмотреть информацию о вещи",
                           lambda: self.app_ref.show_thing_information(index.internalPointer().ref))

            menu.addAction("Показать вещь в пространстве",
                           lambda: self.show_thing_in_space(index))

        menu.exec(self.viewport().mapToGlobal(position))


    def show_thing_in_space(self, index: QModelIndex):
        node = index.internalPointer()
        print(f"NODE: {node.ref}")
        self.app_ref.load_space_from_DB(index.internalPointer().ref.id_parent_space, thing_to_show=node.ref)




    # def open_space_in_main_window(self, index: QModelIndex):
    #     try:
    #         node = index.internalPointer()
    #         if node and node.node_type == NODE_TYPE_SPACE:
    #             self.app_ref.load_space_from_DB(node.ref.id_space)
    #     except Exception as e:
    #         print(e)



# def get_top_space_id(starting_parent_id, cursor):
#     """
#     Рекурсивно находит самое верхнее пространство (у которого id_parent_space IS NULL).
#
#     :param starting_parent_id: исходное id_parent_space
#     :param cursor: psycopg2 курсор с подключением к БД
#     :return: id_space самого верхнего пространства
#     """
#     current_id = starting_parent_id
#
#     while current_id is not None:
#         cursor.execute(
#             "SELECT id_space, id_parent_space FROM spaces.spaces WHERE id_space = %s",
#             (current_id,)
#         )
#         result = cursor.fetchone()
#
#         if result is None:
#             raise ValueError(f"Пространство с id={current_id} не найдено в базе данных")
#
#         current_id, parent_id = result  # current_id теперь id_space текущего пространства
#
#         if parent_id is None:
#             return current_id  # нашли корень
#         else:
#             current_id = parent_id
#
#
# def get_space(id_space: int) -> space.Space:
#     return space.load_space_by_id(id_space)
#
#
# def start():
#     config = connect_DB.load_config()
#     conn = connect_DB.db_connect(config)
#     with conn:
#         with conn.cursor() as cursor:
#             root_id = get_top_space_id(starting_parent_id=59, cursor=cursor)
#             print("Корневое пространство:", root_id)
#
#             return root_id
#
#
#
#
# if __name__ == '__main__':
#     application = QApplication(sys.argv)
#     tree_view = TreeWidget(application)
#     id_top_space = start()
#     sp = get_space(id_top_space)
#
#     tree_view.update_tree(sp)
#
#     tree_view.show()
#
#     sys.exit(application.exec())