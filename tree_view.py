from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QModelIndex
from PyQt6.QtWidgets import QTreeView, QMenu, QAbstractItemView
from tree_model import TreeNode, TreeModel

class TreeWidget(QTreeView):

    node_clicked = pyqtSignal(object)

    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.root_item = TreeNode(None, "root", TreeNode.TYPE_SPACE)
        self.model = TreeModel(self.root_item, self)
        self.setModel(self.model)

        self.app_ref = app

        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)

    def check_permissions_of_user(self, space):
        return self.app_ref.access_manager.can_view(space) or self.app_ref.access_manager.can_edit(space)

    def build_tree_nodes(self, space):
        """Создаёт узел пространства и добавляет только подпространства первого уровня и вещи,
           заменяя название на 'Пространство без доступа', если пользователь не имеет прав."""

        if getattr(space, "state", None) == "DELETED":  # замените ObjectState.DELETED при необходимости
            return None

        permissions = self.check_permissions_of_user(space)

        if not permissions:
            current_node = TreeNode(space, "Пространство без доступа", TreeNode.TYPE_SPACE)
        else:
            current_node = TreeNode(space, space.name, TreeNode.TYPE_SPACE)

        # Добавляем подпространства первого уровня
        for subspace in getattr(space, "subspaces", []):
            if getattr(subspace, "state", None) != "DELETED":
                sub_permissions = self.check_permissions_of_user(subspace)
                if not sub_permissions:
                    child_node = TreeNode(subspace, "Пространство без доступа", TreeNode.TYPE_SPACE)
                else:
                    child_node = TreeNode(subspace, subspace.name, TreeNode.TYPE_SPACE)
                current_node.add_child(child_node)

        # Добавляем вещи
        if permissions:
            for thing in getattr(space, "things", []):
                if getattr(thing, "state", None) != "DELETED":
                    thing_node = TreeNode(thing, thing.name, TreeNode.TYPE_THING)
                    current_node.add_child(thing_node)

        return current_node

    # from PyQt6 import QtWidgets
    #
    # def clear_tree(self):
    #     """Простое очищение дерева"""
    #     self.setModel(None)
    #     self.root_item = None
    #     self.model = None
    #
    #
    # def update_tree(self, parent_space=None):
    #     """Обновляет модель, начиная с нового пространства"""
    #     if parent_space is None or parent_space.state == "DELETED":
    #         self.clear_tree()
    #         return
    #
    #     # Если пространство существует — строим дерево
    #     self.root_item = TreeNode(None, "root", TreeNode.TYPE_SPACE)
    #     root_child = self.build_tree_nodes(parent_space)
    #     if root_child is not None:
    #         self.root_item.add_child(root_child)
    #
    #     self.model = TreeModel(self.root_item, self)
    #     self.setModel(self.model)
    #     self.expandAll()

    def update_tree(self, parent_space=None):
        """Обновляет модель, начиная с нового пространства"""
        self.root_item = TreeNode(None, "root", TreeNode.TYPE_SPACE)

        if parent_space is not None and parent_space.state != "DELETED":
            print("--AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA")
            root_child = self.build_tree_nodes(parent_space)
            if root_child is not None:
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
                           lambda: self.app_ref.show_space_information(item.ref))
            menu.addAction("Посмотреть все вещи в пространстве",
                           lambda: self.app_ref.show_all_things_in_space(item.ref))
            menu.addSeparator()
            menu.addAction("Удалить пространство", lambda: self.delete_space(index))
        elif node_type == TreeNode.TYPE_SPACE:
            menu.addAction("Добавить развертку для подпространства", lambda: self.add_subspace_projection(index))
            menu.addAction("Открыть подпространство как пространство", lambda: self.open_subspace(index))
            menu.addAction("Посмотреть информацию о подпространстве",
                           lambda: self.app_ref.show_space_information(item.ref))
            menu.addAction("Посмотреть информацию о всех вещах в пространстве",
                           lambda: self.app_ref.show_all_things_in_space(item.ref))
            menu.addSeparator()
            menu.addAction("Удалить подпространство", lambda: self.delete_subspace_from_space(index))
        elif node_type == TreeNode.TYPE_THING:
            menu.addAction("Добавить развертку для вещи", lambda: self.add_thing_projection(index))
            menu.addAction("Посмотреть информацию о вещи",
                           lambda: self.app_ref.show_thing_information(item.ref))
            menu.addSeparator()
            menu.addAction("Удалить вещь", lambda: self.delete_thing_from_space(index))

        menu.exec(self.viewport().mapToGlobal(position))

    def find_index_by_ref(self, ref, parent_index=QModelIndex()):
        row_count = self.model.rowCount(parent_index)
        for row in range(row_count):
            index = self.model.index(row, 0, parent_index)
            node = index.internalPointer()
            if node and getattr(node, 'ref', None) == ref:
                return index
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

    def open_subspace(self, index: QModelIndex):
        node = index.internalPointer()
        self.app_ref.open_subspace_as_space(node.ref)

    def delete_subspace_from_space(self, index: QModelIndex):
        node = index.internalPointer()
        if node and node.node_type == TreeNode.TYPE_SPACE:
            self.app_ref.delete_subspace(node.ref)

    def add_thing(self):
        self.app_ref.add_thing()

    def add_thing_projection(self, index: QModelIndex):
        node = index.internalPointer()
        self.app_ref.add_thing_projection(node.ref)

    def delete_thing_from_space(self, index: QModelIndex):
        node = index.internalPointer()
        if node and node.node_type == TreeNode.TYPE_THING:
            self.app_ref.delete_thing(node.ref)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            index = self.indexAt(pos)
            if index.isValid():
                node = index.internalPointer()
                parent_index = index.parent()
                if parent_index.isValid():
                    if node.node_type in (TreeNode.TYPE_SPACE, TreeNode.TYPE_THING):
                        self.app_ref.handle_node_clicked(node.ref)
                        self.app_ref.highlight_subprojections_on_mini_projections(node.ref)

        super().mouseDoubleClickEvent(event)

    def highlight_node(self, thing_or_space):
        index = self.find_index_by_ref(thing_or_space)
        if index.isValid():
            self.setCurrentIndex(index)
            self.scrollTo(index, QAbstractItemView.ScrollHint.PositionAtCenter)
            self.setFocus()
        else:
            print(f"Не удалось найти элемент с ref = {thing_or_space}")