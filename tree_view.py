from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTreeView, QMenu
)
from PyQt6.QtCore import (
    Qt, QAbstractItemModel, QModelIndex, QPoint
)
from PyQt6.QtGui import QIcon
from track_object_state import ObjectState
import sys

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
        child.parent = self

    def child_count(self):
        return len(self.children)

    def child(self, row):
        return self.children[row]

    def row(self):
        if self.parent:
            return self.parent.children.index(self)
        return 0


class TreeModel(QAbstractItemModel):
    def __init__(self, root_item, app_widget):
        super().__init__()
        self.root_item = root_item
        self.app_ref = app_widget

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
        parent_item = item.parent
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
                return QIcon("icons/thing.png")   # путь к иконке вещи

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return "Структура пространства"
        return None


class TreeWidget(QTreeView):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.root_item = TreeNode(None,"root", NODE_TYPE_SPACE)
        self.model = TreeModel(self.root_item, self)
        self.setModel(self.model)

        self.app_ref = app

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)

    def build_tree_nodes(self, space):
        """Создаёт узел пространства и рекурсивно добавляет потомков"""
        current_node = TreeNode(space, space.name, NODE_TYPE_SPACE)

        # Подпространства
        for subspace in getattr(space, "subspaces", []):
            if getattr(subspace, "state", None) != ObjectState.DELETED:
                child_node = self.build_tree_nodes(subspace)
                current_node.add_child(child_node)

        # Вещи
        for thing in getattr(space, "things", []):
            if getattr(thing, "state", None) != ObjectState.DELETED:
                thing_node = TreeNode(thing, thing.name, NODE_TYPE_THING)
                current_node.add_child(thing_node)

        return current_node

    def update_tree(self, parent_space):
        """Обновляет модель, начиная с нового пространства"""
        # Новый root (невидимый) и один видимый child (parent_space)
        self.root_item = TreeNode(None,"root", NODE_TYPE_SPACE)
        root_child = self.build_tree_nodes(parent_space)
        self.root_item.add_child(root_child)

        self.model = TreeModel(self.root_item, self)
        self.setModel(self.model)
        self.expandAll()

    def open_context_menu(self, position: QPoint):
        index = self.indexAt(position)
        if not index.isValid():
            return

        item = index.internalPointer()
        node_type = item.node_type

        menu = QMenu(self)

        if node_type == NODE_TYPE_SPACE:
            menu.addAction("Добавить развертку для подпространства", lambda: self.add_subspace_projection(index))
            #menu.addAction("Добавить вещь", lambda: self.add_item(index))
            menu.addSeparator()
            menu.addAction("Удалить подпространство", lambda: self.delete_subspace_from_space(index))
        elif node_type == NODE_TYPE_THING:
            menu.addAction("Добавить развертку для вещи", lambda: self.add_thing_projection(index))
            menu.addSeparator()
            menu.addAction("Удалить вещь", lambda: self.delete_thing_from_space(index))

        menu.exec(self.viewport().mapToGlobal(position))

    def add_subspace_projection(self, index: QModelIndex):
        node = index.internalPointer()
        self.app_ref.add_subspace_projection(node.ref)

    def delete_subspace_from_space(self, index: QModelIndex):
        node = index.internalPointer()
        if node and node.node_type == NODE_TYPE_SPACE:
            self.app_ref.delete_subspace(node.ref)

    def add_thing_projection(self, index: QModelIndex):
        node = index.internalPointer()
        self.app_ref.add_thing_projection(node.ref)

    def delete_thing_from_space(self, index: QModelIndex):
        node = index.internalPointer()
        if node and node.node_type == NODE_TYPE_THING:
            self.app_ref.delete_thing(node.ref)

    # def add_item(self, index: QModelIndex):
    #     print("Добавить вещь")






# if __name__ == "__main__":
#     app = QApplication(sys.argv)
#     widget = TreeWidget()
#     widget.show()
#     sys.exit(app.exec())
