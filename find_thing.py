from PyQt6.QtWidgets import (QPushButton, QVBoxLayout, QApplication, QFrame,
                             QDialog, QCheckBox, QListWidget, QListWidgetItem,
                             QComboBox, QRadioButton, QButtonGroup, QLineEdit, QHBoxLayout, QLabel
                             )
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import Qt
import sys
import all_spaces_in_DB
import connect_DB as connection
import psycopg2


class FindThing(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Найти вещь")
        self.setWindowIcon(QIcon("icons/mini_logo.png"))
        self.selected_file = ""

        self.spaces_in_DB = all_spaces_in_DB.load_all_spaces_from_DB()
        print(self.spaces_in_DB)
        spaces_names = [space[1] for space in self.spaces_in_DB]
        print(spaces_names)

        self.layout = QVBoxLayout()

        self.exact_match = QCheckBox("Искать точное совпадение")

        self.radio_name_and_description = QRadioButton("Искать и в названиях, и в описаниях")
        self.radio_name = QRadioButton("Искать только в названиях")
        self.radio_description = QRadioButton("Искать только в описаниях")
        group = QButtonGroup(self)
        group.addButton(self.radio_name_and_description, 1)
        group.addButton(self.radio_name, 2)
        group.addButton(self.radio_description, 3)
        self.radio_name_and_description.setChecked(True)
        self.space_for_find = QComboBox()
        self.thing_to_find = QLineEdit()
        self.find_button = QPushButton("Найти")

        self.layout.addWidget(self.exact_match)
        self.layout.addWidget(self.make_separator())

        self.layout.addWidget(self.radio_name_and_description)
        self.layout.addWidget(self.radio_name)
        self.layout.addWidget(self.radio_description)

        self.layout.addWidget(self.make_separator())

        self.choose_space_label = QLabel("Выберете пространства для поиска:")
        self.layout.addWidget(self.choose_space_label)

        self.buttons_layout = QHBoxLayout()
        self.select_all_button = QPushButton("Выбрать все")
        self.buttons_layout.addWidget(self.select_all_button)

        self.select_all_button.clicked.connect(self.select_all_spaces)

        self.deselect_all_button = QPushButton("Снять все")
        self.buttons_layout.addWidget(self.deselect_all_button)
        self.deselect_all_button.clicked.connect(self.deselect_all_spaces)

        self.layout.addLayout(self.buttons_layout)

        self.list_widget = QListWidget()
        self.layout.addWidget(self.list_widget)
        for name in spaces_names:
            item = QListWidgetItem(name)
            item.setCheckState(Qt.CheckState.Unchecked)
            self.list_widget.addItem(item)

        self.things_to_find_label = QLabel("Укажите вещи для поиска:")
        self.layout.addWidget(self.things_to_find_label)

        self.layout.addWidget(self.thing_to_find)
        self.layout.addWidget(self.find_button)

        self.setLayout(self.layout)

        self.find_button.clicked.connect(self.find_thing_in_DB)

    @staticmethod
    def make_separator():
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setFrameShadow(QFrame.Shadow.Sunken)
        sep.setLineWidth(1)
        return sep


    def select_all_spaces(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setCheckState(Qt.CheckState.Checked)


    def deselect_all_spaces(self):
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            item.setCheckState(Qt.CheckState.Unchecked)


    def get_parameters_for_search(self):
        checked_spaces_id = []
        for i in range(self.list_widget.count()):
            item = self.list_widget.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                checked_spaces_id.append(self.spaces_in_DB[i][0])

        search_text = self.thing_to_find.text()

        exact_match = self.exact_match.isChecked()

        if self.radio_name.isChecked():
            search_mode = "name"
        elif self.radio_description.isChecked():
            search_mode = "description"
        else:
            search_mode = "both"

        parameters_for_search = [search_text, exact_match, search_mode, checked_spaces_id]
        #print(parameters_for_search)

        return parameters_for_search

    @staticmethod
    def find_things(search_text, exact_match, search_mode, space_ids):

        try:
            """
            search_text - строка из QLineEdit
            exact_match - bool (QCheckBox)
            search_mode - 'name' | 'description' | 'both' (QRadioButton group)
            space_ids   - список id выбранных пространств из QListWidget
            """

            if not search_text.strip():
                return []  # если пустой поиск, возвращаем пустой список

            config = connection.load_config()
            conn = connection.db_connect(config)
            cur = conn.cursor()

            params = []

            # -----------------------
            # Строим WHERE для поиска
            # -----------------------
            if exact_match:
                # Точное совпадение по всей строке
                value = search_text.strip()
                if search_mode == "name":
                    where_clause = "t.thing_name = %s"
                    params.append(value)
                elif search_mode == "description":
                    where_clause = "t.thing_description = %s"
                    params.append(value)
                else:  # both
                    where_clause = "(t.thing_name = %s OR t.thing_description = %s)"
                    params.extend([value, value])
            else:
                # Не точное совпадение: разбиваем на слова и ищем каждое через ILIKE
                words = search_text.strip().split()
                word_clauses = []

                for word in words:
                    word_value = f"%{word}%"
                    if search_mode == "name":
                        word_clauses.append("t.thing_name ILIKE %s")
                        params.append(word_value)
                    elif search_mode == "description":
                        word_clauses.append("t.thing_description ILIKE %s")
                        params.append(word_value)
                    else:  # both
                        word_clauses.append("(t.thing_name ILIKE %s OR t.thing_description ILIKE %s)")
                        params.extend([word_value, word_value])

                # Одно из слов должно присутствовать
                where_clause = " OR ".join(word_clauses)

            # -----------------------
            # Фильтр по выбранным пространствам
            # -----------------------
            if space_ids:
                where_clause += " AND t.id_parent_space = ANY(%s)"
                params.append(space_ids)

            # -----------------------
            # Формируем полный запрос
            # -----------------------
            # noinspection SqlNoDataSourceInspection
            query = f"""
                SELECT t.id_thing, t.thing_name, t.thing_description, s.id_space
                FROM spaces.things t
                JOIN spaces.spaces s ON t.id_parent_space = s.id_space
                WHERE {where_clause}
                ORDER BY t.thing_name;
            """

            cur.execute(query, params)
            results = cur.fetchall()
            cur.close()
            conn.close()
            return results
        except psycopg2.Error as e:
            print(e)


    def find_thing_in_DB(self):
        parameters_for_search = self.get_parameters_for_search()

        results = self.find_things(
            search_text=parameters_for_search[0],
            exact_match=parameters_for_search[1],
            search_mode=parameters_for_search[2],
            space_ids=parameters_for_search[3]
        )
        print(f"results: {results}")
        for r in results:
            print(r)

        self.accept()
        return results