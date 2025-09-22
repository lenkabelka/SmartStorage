from PyQt6.QtWidgets import (QPushButton, QVBoxLayout, QApplication, QFrame,
                             QDialog, QCheckBox, QListWidget, QListWidgetItem, QStackedLayout,
                             QComboBox, QRadioButton, QButtonGroup, QLineEdit, QHBoxLayout, QLabel, QMessageBox
                             )
from PyQt6.QtGui import QIcon, QFont
from PyQt6.QtCore import Qt
import sys
import all_spaces_in_DB
import connect_DB as connection
import psycopg2
import bcrypt


class LogIn(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Войдите или зарегистрируйтесь")
        self.setWindowIcon(QIcon("icons/mini_logo.png"))

        font = QFont()
        font.setPointSize(14)
        self.setFont(font)

        self.stack_layout = QStackedLayout()

        self.login_view = QFrame()
        self.login_layout = QVBoxLayout()
        self.login_view.setLayout(self.login_layout)

        self.login_login = QLineEdit(self)
        self.password_login = QLineEdit(self)
        self.login_login.setPlaceholderText("Имя пользователя")
        self.password_login.setPlaceholderText("Пароль")

        self.button_layout_login = QHBoxLayout()
        self.login_button = QPushButton(self)
        self.login_button.setText("Войти")
        self.register_button = QPushButton(self)
        self.register_button.setText("Зарегистрироваться")

        self.login_layout.addWidget(self.login_login)
        self.login_layout.addWidget(self.password_login)

        self.button_layout_login.addWidget(self.login_button)
        self.button_layout_login.addWidget(self.register_button)
        self.login_layout.addLayout(self.button_layout_login)

        self.register_button.clicked.connect(self.register_page)

    ############################################################

        self.register_view = QFrame()
        self.register_layout = QVBoxLayout()
        self.register_view.setLayout(self.register_layout)

        self.login_register = QLineEdit(self)
        self.password_register = QLineEdit(self)

        self.login_register.setPlaceholderText("Имя пользователя")
        self.password_register.setPlaceholderText("Пароль")

        self.email_register = QLineEdit(self)
        self.email_register.setPlaceholderText("E-Mail")

        self.register_register_button = QPushButton(self)
        self.register_register_button.setText("Зарегистрироваться")

        self.already_registered_button = QPushButton()
        self.already_registered_button.setText("Уже зарегистрирован, войти")

        self.already_registered_button.clicked.connect(self.login_page)

        self.button_layout_register = QHBoxLayout()
        self.button_layout_register.addWidget(self.register_register_button)
        self.button_layout_register.addWidget(self.already_registered_button)

        self.register_layout.addWidget(self.login_register)
        self.register_layout.addWidget(self.password_register)
        self.register_layout.addWidget(self.email_register)
        self.register_layout.addLayout(
            self.button_layout_register)



        self.stack_layout.addWidget(self.login_view)
        self.stack_layout.addWidget(self.register_view)


        self.stack_layout.setCurrentIndex(0)
        self.setLayout(self.stack_layout)


    def login_page(self):
        self.stack_layout.setCurrentIndex(0)


    def register_page(self):
        self.stack_layout.setCurrentIndex(1)


    def is_userName_available(self):
        username = self.login_login.text()
        password = self.password_login.text()


    def save_user(self):

        username = self.login_login.text()
        password = self.password_login.text()

        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode(), salt).decode()

        try:

            config = connection.load_config()
            conn = connection.db_connect(config)

            cur = conn.cursor()
            # noinspection SqlNoDataSourceInspection
            cur.execute("SELECT 1 FROM spaces.users WHERE username = %s", (username,))
            exists = cur.fetchone()

            if exists:
                QMessageBox.warning(self, "Имя занято",
                                    "Пользователь с таким именем уже существует!")
                print("This login is busy")
            else:
                # noinspection SqlNoDataSourceInspection
                cur.execute("INSERT INTO spaces.users (username, password_hash) VALUES (%s, %s)",
                            (username, password_hash))
                conn.commit()
                print("User saved successfully!")

            cur.close()
            conn.close()

        except Exception as e:
            print(f"Error: {e}")
            conn.rollback()


    def is_user_in_DB(user_name, password):

        try:

            config = connection.load_config()
            conn = connection.db_connect(config)

            with conn.cursor() as cur:
                # noinspection SqlNoDataSourceInspection
                cur.execute("SELECT * FROM spaces.users "
                            "WHERE user_nickname = %s", (user_name,))

                user = cur.fetchone()

                if user is None:
                    return False

                return bcrypt.checkpw(password.encode(), user[2].encode())

        except Exception as e:
            print(f"Error: {e}")
            return False


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = LogIn()
    window.show()
    sys.exit(app.exec())