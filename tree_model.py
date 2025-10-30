from PyQt6.QtCore import Qt, QModelIndex, QAbstractItemModel
from PyQt6.QtGui import QIcon


class TreeNode:
    TYPE_SPACE = "space"
    TYPE_THING = "thing"

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
        parent_item = getattr(item, 'thing_or_space_parent', None)
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
            if item.node_type == TreeNode.TYPE_SPACE:
                return QIcon("icons/space.png")
            elif item.node_type == TreeNode.TYPE_THING:
                return QIcon("icons/thing_1.jpg")

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return "Структура пространства"
        return None