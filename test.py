from PyQt6.QtCore import Qt, QModelIndex, QAbstractItemModel, QPoint
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTreeView, QMenu,
    QVBoxLayout, QWidget
)
from typing import Any
from PyQt6.QtCore import Qt, QModelIndex


NODE_TYPE_SPACE = "space"
NODE_TYPE_ITEM = "item"

class TreeItem:
    def __init__(self, name, node_type, parent=None):
        self.name = name
        self.node_type = node_type
        self.parent = parent
        self.children = []


        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)

    def open_context_menu(self, position: QPoint):
        index: QModelIndex = self.indexAt(position)
        if not index.isValid():
            return

        item = index.internalPointer()
        node_type = item.node_type

        menu = QMenu(self)

        if node_type == NODE_TYPE_SPACE:
            menu.addAction("Добавить подпространство", lambda: self.add_space(index))
            menu.addAction("Добавить вещь", lambda: self.add_item(index))
            menu.addSeparator()
            menu.addAction("Удалить пространство", lambda: self.delete_item(index))

        elif node_type == NODE_TYPE_ITEM:
            menu.addAction("Переименовать вещь", lambda: self.rename_item(index))
            menu.addAction("Удалить вещь", lambda: self.delete_item(index))

        menu.exec(self.viewport().mapToGlobal(position))

    def child_count(self):
        return len(self.children)

    def child(self, row):
        return self.children[row]

    def add_child(self, item):
        self.children.append(item)
        item.parent = self

    def remove_child(self, row):
        del self.children[row]

    def row(self):
        if self.parent:
            return self.parent.children.index(self)
        return 0

class TreeModel(QAbstractItemModel):
    def __init__(self, root_item):
        super().__init__()
        self.root_item = root_item

    # rowCount
    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        parent_item = self.get_item(parent)
        return parent_item.child_count()

    # columnCount
    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return 1

    # index
    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        parent_item = self.get_item(parent)
        if 0 <= row < parent_item.child_count():
            child_item = parent_item.child(row)
            return self.createIndex(row, column, child_item)
        return QModelIndex()

    # parent
    def parent(self, index: QModelIndex) -> QModelIndex:
        if not index.isValid():
            return QModelIndex()
        child_item = self.get_item(index)
        parent_item = child_item.parent
        if not parent_item or parent_item == self.root_item:
            return QModelIndex()
        return self.createIndex(parent_item.row(), 0, parent_item)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        item = self.get_item(index)
        if role == Qt.ItemDataRole.DisplayRole:
            return item.name
        if role == Qt.ItemDataRole.UserRole:
            return item.node_type
        return None

    def flags(self, index):
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable | Qt.ItemFlag.ItemIsEditable

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:
        if role == Qt.ItemDataRole.EditRole and index.isValid():
            item = self.get_item(index)
            item.name = value
            self.dataChanged.emit(index, index, [role])
            return True
        return False

    def insertItem(self, parent_index: QModelIndex, item: "TreeItem") -> bool:
        parent_item = self.get_item(parent_index)
        row = parent_item.child_count()
        self.beginInsertRows(parent_index, row, row)
        parent_item.add_child(item)
        self.endInsertRows()
        return True

    def removeRow(self, row, parent=QModelIndex()):
        parent_item = self.get_item(parent)
        self.beginRemoveRows(parent, row, row)
        parent_item.remove_child(row)
        self.endRemoveRows()
        return True

    def get_item(self, index):
        if index.isValid():
            return index.internalPointer()
        return self.root_item

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return "Структура пространства"
        return None



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("QAbstractItemModel: Пространства и вещи")

        self.tree = QTreeView()
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.open_context_menu)

        # Корень модели
        root = TreeItem("Квартира", NODE_TYPE_SPACE)
        kitchen = TreeItem("Кухня", NODE_TYPE_SPACE)
        fridge = TreeItem("Холодильник", NODE_TYPE_SPACE)
        spoon = TreeItem("Ложка", NODE_TYPE_ITEM)
        milk = TreeItem("Молоко", NODE_TYPE_ITEM)

        root.add_child(kitchen)
        kitchen.add_child(fridge)
        kitchen.add_child(spoon)
        fridge.add_child(milk)

        self.model = TreeModel(root)
        self.tree.setModel(self.model)
        self.tree.expandAll()

        layout = QVBoxLayout()
        layout.addWidget(self.tree)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    # def open_context_menu(self, position):
    #     index = self.tree.indexAt(position)
    #     if not index.isValid():
    #         return
    #
    #     item = index.internalPointer()
    #     node_type = item.node_type
    #
    #     menu = QMenu()
    #
    #     if node_type == NODE_TYPE_SPACE:
    #         menu.addAction("Добавить подпространство", lambda: self.add_space(index))
    #         menu.addAction("Добавить вещь", lambda: self.add_item(index))
    #         menu.addSeparator()
    #         menu.addAction("Удалить пространство", lambda: self.delete_item(index))
    #
    #     elif node_type == NODE_TYPE_ITEM:
    #         menu.addAction("Переименовать вещь", lambda: self.rename_item(index))
    #         menu.addAction("Удалить вещь", lambda: self.delete_item(index))
    #
    #     menu.exec(self.tree.viewport().mapToGlobal(position))

    def add_space(self, parent_index):
        new_item = TreeItem("Новое пространство", NODE_TYPE_SPACE)
        self.model.insertRow(0, parent_index, new_item)
        self.tree.expand(parent_index)

    def add_item(self, parent_index):
        new_item = TreeItem("Новая вещь", NODE_TYPE_ITEM)
        self.model.insertRow(0, parent_index, new_item)
        self.tree.expand(parent_index)

    def delete_item(self, index):
        parent_index = self.model.parent(index)
        self.model.removeRow(index.row(), parent_index)

    def rename_item(self, index):
        self.tree.edit(index)

# Запуск
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(400, 300)
    window.show()
    sys.exit(app.exec())
