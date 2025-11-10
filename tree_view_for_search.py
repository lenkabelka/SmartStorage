from PyQt6.QtCore import Qt, QPoint, QModelIndex
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QTreeView, QMenu
from tree_model import TreeNode, TreeModel

class TreeWidgetForSearch(QTreeView):
    def __init__(self, app, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Дерево пространства")
        self.setWindowIcon(QIcon("icons/mini_logo.png"))
        self.root_item = TreeNode(None, "root", TreeNode.TYPE_SPACE)
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

    def check_permissions_of_user(self, space) -> bool:
        return self.app_ref.access_manager.can_view(space) or self.app_ref.access_manager.can_edit(space)

    def build_tree_nodes(self, space_in_DB):
        permissions = self.check_permissions_of_user(space_in_DB)

        if not permissions:
            return TreeNode(space_in_DB, "Пространство без доступа", TreeNode.TYPE_SPACE)

        current_node = TreeNode(space_in_DB, space_in_DB.name, TreeNode.TYPE_SPACE)

        # Обрабатываем вещи
        if permissions:
            for thing in sorted(getattr(space_in_DB, "things", []), key=lambda t: t.name.lower()):
                thing_node = TreeNode(thing, thing.name, TreeNode.TYPE_THING)
                current_node.add_child(thing_node)

        # Рекурсивно обрабатываем подпространства
        for subspace in sorted(getattr(space_in_DB, "subspaces", []), key=lambda s: s.name.lower()):
            child_node = self.build_tree_nodes(subspace)
            current_node.add_child(child_node)

        # # Обрабатываем вещи
        # if permissions:
        #     for thing in sorted(getattr(space_in_DB, "things", []), key=lambda t: t.name.lower()):
        #         thing_node = TreeNode(thing, thing.name, TreeNode.TYPE_THING)
        #         current_node.add_child(thing_node)

        return current_node

    def update_tree(self, space_in_DB=None, highlight_name: str = None):
        """Обновляет модель, начиная с нового пространства, и подсвечивает указанную вещь"""
        self.root_item = TreeNode(None, "root", TreeNode.TYPE_SPACE)

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
                self.scrollTo(index)

    def find_index_by_name(self, name: str):
        """Ищет индекс по имени вещи"""

        def recursive_search(parent_index):
            rows = self.model.rowCount(parent_index)
            for row in range(rows):
                index = self.model.index(row, 0, parent_index)
                if index.isValid():
                    item_name = index.data()
                    if item_name == name:
                        return index
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

        if node_type == TreeNode.TYPE_SPACE:
            menu.addAction(
                "Открыть пространство для редактирования",
                lambda: self.app_ref.load_space_from_DB(item.ref.id_space)
            )
            menu.addAction(
                "Посмотреть информацию о пространстве",
                lambda: self.app_ref.show_space_information(item.ref)
            )
            menu.addAction("Посмотреть информацию о всех вещах в пространстве",
                           lambda: self.app_ref.show_all_things_in_space(item.ref))

        elif node_type == TreeNode.TYPE_THING:
            menu.addAction(
                "Посмотреть информацию о вещи",
                lambda: self.app_ref.show_thing_information(item.ref)
            )
            menu.addAction(
                "Показать вещь в пространстве",
                lambda: self.show_thing_in_space(index)
            )

        menu.exec(self.viewport().mapToGlobal(position))

    def show_thing_in_space(self, index: QModelIndex):
        node = index.internalPointer()
        print(f"NODE: {node.ref}")

        # TODO: вещь не подсветится, если пространство новое
        self.app_ref.load_space_from_DB(
            index.internalPointer().ref.id_parent_space,
            thing_to_show=node.ref
        )