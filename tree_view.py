from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTreeView, QMenu, QAbstractItemView
)
from PyQt6.QtCore import (
    Qt, QAbstractItemModel, QModelIndex, QPoint, pyqtSignal
)
from PyQt6.QtGui import QIcon
from track_object_state import ObjectState


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


class TreeWidget(QTreeView):

    node_clicked = pyqtSignal(object)

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.root_item = TreeNode(None,"root", NODE_TYPE_SPACE)
        self.model = TreeModel(self.root_item, self)
        self.setModel(self.model)

        self.app_ref = app

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)


    def build_tree_nodes(self, space):
        """Создаёт узел пространства и добавляет только подпространства первого уровня и вещи"""

        if getattr(space, "state", None) == ObjectState.DELETED:
            print("Пространство удалено — узел не создаём")
            return None  # Не создавать узел для удалённого пространства

        current_node = TreeNode(space, space.name, NODE_TYPE_SPACE)

        # Добавляем подпространства первого уровня — без рекурсии
        for subspace in getattr(space, "subspaces", []):
            if getattr(subspace, "state", None) != ObjectState.DELETED:
                child_node = TreeNode(subspace, subspace.name, NODE_TYPE_SPACE)
                current_node.add_child(child_node)

        # Добавляем вещи
        for thing in getattr(space, "things", []):
            if getattr(thing, "state", None) != ObjectState.DELETED:
                thing_node = TreeNode(thing, thing.name, NODE_TYPE_THING)
                current_node.add_child(thing_node)

        return current_node


    def update_tree(self, parent_space=None):
        """Обновляет модель, начиная с нового пространства"""
        # Новый root (невидимый)
        self.root_item = TreeNode(None, "root", NODE_TYPE_SPACE)

        if parent_space is not None:
            root_child = self.build_tree_nodes(parent_space)
            if root_child is not None:
                self.root_item.add_child(root_child)
            else:
                print("Корневое пространство удалено. Показывается только скрытый root.")

        self.model = TreeModel(self.root_item, self)
        self.setModel(self.model)
        self.expandAll()


    def open_context_menu(self, position: QPoint):
        index = self.indexAt(position)
        if not index.isValid():
            return

        item = index.internalPointer()
        node_type = item.node_type

        is_root = not index.parent().isValid()

        menu = QMenu(self)

        if is_root:
            if self.app_ref.parent_space.current_projection is None:
                menu.addAction("Добавить проекцию пространства", lambda: self.add_space_projection())
            else:
                menu.addAction("Изменить проекцию пространства", lambda: self.add_space_projection())
            menu.addAction("Открыть родительское пространство", lambda: self.open_parent_space())
            menu.addAction("Добавить подпространство", lambda: self.add_subspace())
            menu.addAction("Добавить вещь", lambda: self.add_thing())
            menu.addAction("Посмотреть информацию о пространстве",
                           lambda: self.app_ref.show_space_information(index.internalPointer().ref))
            menu.addAction("Посмотреть все вещи в пространстве",
                           lambda: self.app_ref.show_all_things_in_space(index.internalPointer().ref))
            menu.addSeparator()
            menu.addAction("Удалить пространство", lambda: self.delete_space(index))
        elif node_type == NODE_TYPE_SPACE:
            menu.addAction("Добавить развертку для подпространства", lambda: self.add_subspace_projection(index))
            menu.addAction("Открыть подпространство как пространство", lambda: self.open_subspace_as_space(index))
            menu.addAction("Посмотреть информацию о подпространстве",
                           lambda: self.app_ref.show_space_information(index.internalPointer().ref))
            menu.addAction("Посмотреть все вещи в пространстве",
                           lambda: self.app_ref.show_all_things_in_space(index.internalPointer().ref))
            menu.addSeparator()
            menu.addAction("Удалить подпространство", lambda: self.delete_subspace_from_space(index))
        elif node_type == NODE_TYPE_THING:
            menu.addAction("Добавить развертку для вещи", lambda: self.add_thing_projection(index))
            menu.addAction("Посмотреть информацию о вещи",
                           lambda: self.app_ref.show_thing_information(index.internalPointer().ref))
            menu.addSeparator()
            menu.addAction("Удалить вещь", lambda: self.delete_thing_from_space(index))

        menu.exec(self.viewport().mapToGlobal(position))


    def find_index_by_ref(self, ref, parent_index=QModelIndex()):
        model = self.model
        row_count = model.rowCount(parent_index)
        for row in range(row_count):
            index = model.index(row, 0, parent_index)
            node = index.internalPointer()
            if node and getattr(node, 'ref', None) == ref:
                return index
            # Рекурсивный поиск
            child_index = self.find_index_by_ref(ref, index)
            if child_index and child_index.isValid():
                return child_index
        return QModelIndex()


    def open_parent_space(self):
        self.app_ref.load_parent_space_from_DB()


    def delete_space(self, index: QModelIndex):
        node = index.internalPointer()
        self.app_ref.delete_space(node.ref)


    def add_space_projection(self):
        self.app_ref.add_space_projection()


    def add_subspace(self):
        self.app_ref.add_subspace()


    def add_subspace_projection(self, index: QModelIndex):
        node = index.internalPointer()
        self.app_ref.add_subspace_projection(node.ref)


    def open_subspace_as_space(self, index: QModelIndex):
        node = index.internalPointer()
        self.app_ref.open_space(node.ref)


    def delete_subspace_from_space(self, index: QModelIndex):
        node = index.internalPointer()
        if node and node.node_type == NODE_TYPE_SPACE:
            self.app_ref.delete_subspace(node.ref)


    def add_thing(self):
        self.app_ref.add_thing()


    def add_thing_projection(self, index: QModelIndex):
        node = index.internalPointer()
        self.app_ref.add_thing_projection(node.ref)


    def delete_thing_from_space(self, index: QModelIndex):
        node = index.internalPointer()
        if node and node.node_type == NODE_TYPE_THING:
            self.app_ref.delete_thing(node.ref)


    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            index = self.indexAt(pos)
            if index.isValid():
                node = index.internalPointer()
                # Проверяем, что узел не root — у root нет родителя, или он равен root_item
                parent_index = index.parent()
                if parent_index.isValid():  # есть родитель (значит не root)
                    if node.node_type in (NODE_TYPE_SPACE, NODE_TYPE_THING):
                        self.node_clicked.emit(node.ref)

                        self.app_ref.highlight_subprojections_on_mini_projections(node.ref)

        super().mouseDoubleClickEvent(event)


    def highlight_node(self, thing_or_space):
        index = self.find_index_by_ref(thing_or_space)
        if index.isValid():
            self.setCurrentIndex(index)  # выделяет элемент
            self.scrollTo(index, QAbstractItemView.ScrollHint.PositionAtCenter)  # скроллит
            self.setFocus()
        else:
            print(f"Не удалось найти элемент с ref = {thing_or_space}")