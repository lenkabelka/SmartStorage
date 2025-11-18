from PyQt6.QtCore import Qt, QPoint, pyqtSignal, QModelIndex
from PyQt6.QtWidgets import QTreeView, QMenu, QAbstractItemView
from tree_model import TreeNode, TreeModel
from track_object_state import ObjectState

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

        if getattr(space, "state", None) == ObjectState.DELETED:
            return None

        permissions = self.check_permissions_of_user(space)

        if not permissions:
            current_node = TreeNode(space, "Пространство без доступа", TreeNode.TYPE_SPACE)
        else:
            current_node = TreeNode(space, space.name, TreeNode.TYPE_SPACE)

        # Добавляем вещи
        if permissions:
            for thing in sorted(getattr(space, "things", []), key=lambda t: t.name.lower()):
                if getattr(thing, "state", None) != ObjectState.DELETED:
                    thing_node = TreeNode(thing, thing.name, TreeNode.TYPE_THING)
                    current_node.add_child(thing_node)

        # Добавляем подпространства первого уровня
        for subspace in sorted(getattr(space, "subspaces", []), key=lambda s: s.name.lower()):
            if getattr(subspace, "state", None) != ObjectState.DELETED:
                sub_permissions = self.check_permissions_of_user(subspace)
                if not sub_permissions:
                    child_node = TreeNode(subspace, "Пространство без доступа", TreeNode.TYPE_SPACE)
                else:
                    child_node = TreeNode(subspace, subspace.name, TreeNode.TYPE_SPACE)
                current_node.add_child(child_node)

        # # Добавляем вещи
        # if permissions:
        #     for thing in sorted(getattr(space, "things", []), key=lambda t: t.name.lower()):
        #         if getattr(thing, "state", None) != ObjectState.DELETED:
        #             thing_node = TreeNode(thing, thing.name, TreeNode.TYPE_THING)
        #             current_node.add_child(thing_node)

        return current_node

    def update_tree(self, parent_space=None):
        """Обновляет модель, начиная с нового пространства"""
        self.root_item = TreeNode(None, "root", TreeNode.TYPE_SPACE)

        if parent_space is not None and parent_space.state != "DELETED":
            root_child = self.build_tree_nodes(parent_space)
            if root_child is not None:
                #print(f"root_child: {root_child}")
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
            if self.app_ref.main_projection is None:
                add_new_projection = True
                menu.addAction("Добавить проекцию пространства", lambda: self.add_space_projection(add_new_projection))
            else:
                add_new_projection = False
                menu.addAction("Изменить проекцию пространства", lambda: self.add_space_projection(add_new_projection))
            menu.addAction("Открыть родительское пространство", lambda: self.open_parent_space())
            menu.addAction("Добавить подпространство", lambda: self.add_subspace())
            menu.addAction("Добавить вещь", lambda: self.add_thing())
            menu.addAction("Посмотреть информацию о пространстве",
                           lambda: self.app_ref.show_space_information(item.ref))
            menu.addAction("Посмотреть информацию о всех вещах в пространстве",
                           lambda: self.app_ref.show_all_things_in_space(item.ref))
            menu.addAction("Изменить информацию о пространстве",
                           lambda: self.app_ref.change_space_information(item.ref))
            menu.addAction("Перенести пространство в другое пространство",
                           lambda: self.app_ref.change_parent_space_of_thing_or_space(item.ref))
            menu.addSeparator()
            menu.addAction("Удалить пространство", lambda: self.app_ref.delete_space())
        elif node_type == TreeNode.TYPE_SPACE:
            menu.addAction("Добавить проекцию для подпространства", lambda: self.add_subspace_projection(index))
            menu.addAction("Открыть подпространство как пространство", lambda: self.open_subspace(index))
            menu.addAction("Посмотреть информацию о подпространстве",
                           lambda: self.app_ref.show_space_information(item.ref))
            menu.addAction("Изменить информацию о подпространстве",
                           lambda: self.app_ref.change_space_information(item.ref))
            menu.addAction("Посмотреть информацию о всех вещах в подпространстве",
                           lambda: self.app_ref.show_all_things_in_space(item.ref))
            menu.addAction("Перенести подпространство в другое пространство",
                           lambda: self.app_ref.change_parent_space_of_thing_or_space(item.ref))
            menu.addSeparator()
            menu.addAction("Удалить подпространство", lambda: self.delete_subspace_from_space(index))
        elif node_type == TreeNode.TYPE_THING:
            menu.addAction("Добавить проекцию для вещи", lambda: self.add_thing_projection(index))
            menu.addAction("Посмотреть информацию о вещи",
                           lambda: self.app_ref.show_thing_information(item.ref))
            menu.addAction("Изменить информацию о вещи", lambda: self.app_ref.change_thing_information(item.ref))
            menu.addAction("Перенести вещь в другое пространство",
                           lambda: self.app_ref.change_parent_space_of_thing_or_space(item.ref))
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

    def add_space_projection(self, add_new_projection):
        self.app_ref.add_space_projection(add_new_projection=add_new_projection)

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


    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            index = self.indexAt(pos)
            if index.isValid():
                node = index.internalPointer()
                parent_index = index.parent()

                if parent_index.isValid():
                    # Узел с родителем - подсвечиваем
                    if node.node_type in (TreeNode.TYPE_SPACE, TreeNode.TYPE_THING):
                        self.app_ref.handle_node_clicked(node.ref)
                        self.app_ref.highlight_subprojections_on_mini_projections(node.ref)
                else:
                    # Верхний уровень - очищаем подсветку
                    self.app_ref.clear_highlights_on_main_and_mini_scenes()

        super().mousePressEvent(event)


    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down):
            super().keyPressEvent(event)
            # выбранный элемент
            index = self.currentIndex()
            if index.isValid():
                node = index.internalPointer()
                parent_index = index.parent()

                if parent_index.isValid():
                    # Узел с родителем - подсвечиваем
                    if node and node.node_type in (TreeNode.TYPE_SPACE, TreeNode.TYPE_THING):
                        self.app_ref.handle_node_clicked(node.ref)
                        self.app_ref.highlight_subprojections_on_mini_projections(node.ref)
                else:
                    # Верхний уровень - очищаем подсветку
                    self.app_ref.clear_highlights_on_main_and_mini_scenes()
        else:
            super().keyPressEvent(event)  # для остальных клавиш


    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            pos = event.position().toPoint()
            index = self.indexAt(pos)
            if index.isValid():
                node = index.internalPointer()
                parent_index = index.parent()
                if index.isValid():
                    self.app_ref.clear_highlights_on_main_and_mini_scenes()
                if parent_index.isValid():
                    if node.node_type == TreeNode.TYPE_SPACE:
                        self.app_ref.open_subspace_as_space(node.ref)
        super().mouseDoubleClickEvent(event)


    def highlight_node(self, thing_or_space):
        index = self.find_index_by_ref(thing_or_space)
        if index.isValid():
            self.setCurrentIndex(index)
            self.scrollTo(index, QAbstractItemView.ScrollHint.PositionAtCenter)
            #self.setFocus()
        else:
            print(f"Не удалось найти элемент с ref = {thing_or_space}")