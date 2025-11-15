from PyQt6.QtWidgets import (
    QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit, QFrame, QDialog,
    QMessageBox, QStackedLayout
)
from PyQt6.QtGui import QIcon, QFont, QRegularExpressionValidator, QAction
from PyQt6.QtCore import QRegularExpression
import bcrypt
import connect_DB as connection
import user as usr
import utils

class LogIn(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Войдите или зарегистрируйтесь")
        self.setWindowIcon(QIcon(utils.resource_path("icons/mini_logo.png")))


        # Валидация
        nickname_regex = QRegularExpression("^[A-Za-zА-Яа-яЁё0-9]{1,25}$")
        email_regex = QRegularExpression("^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$")
        password_regex = QRegularExpression("^[A-Za-zА-Яа-яЁё0-9]{1,25}$")

        username_validator = QRegularExpressionValidator(nickname_regex, self)
        password_validator = QRegularExpressionValidator(password_regex, self)
        email_validator = QRegularExpressionValidator(email_regex, self)

        # Шрифт
        font = QFont()
        font.setPointSize(14)
        self.setFont(font)

        self.setStyleSheet("""
            QLineEdit {
                border: 2px solid gray;  /* сама рамка */
                border-radius: 5px;      /* скругление углов */
                padding: 3px;            /* отступ текста от рамки */
            }
            QPushButton {
                border: 3px solid gray;  /* меняется при фокусе */
                padding: 12px;            /* отступ текста от рамки */
                border-radius: 5px;      /* скругление углов */
            }
            QPushButton:hover {
                border: 4px solid #35a0a3;  /* меняется при фокусе */
            }
        """)

        # Иконки глазика
        self.icon_show = QIcon(utils.resource_path("icons/opened_eye.ico"))
        self.icon_hide = QIcon(utils.resource_path("icons/closed_eye.ico"))

        # Стек для страниц
        self.stack_layout = QStackedLayout()
        self._setup_login_view(username_validator, password_validator)
        self._setup_register_view(username_validator, password_validator, email_validator)
        self.stack_layout.setCurrentIndex(0)
        self.setLayout(self.stack_layout)

        # Пользователь после успешного входа или регистрации
        self._user: usr.User | None = None

    # ------------------- LOGIN VIEW -------------------
    def _setup_login_view(self, username_validator, password_validator):
        self.login_view = QFrame()
        layout = QVBoxLayout()
        self.login_view.setLayout(layout)

        self.login_login = QLineEdit("Konstantin")
        self.login_login.setPlaceholderText("Имя пользователя")

        self.password_login = QLineEdit("kuzmin")
        self.password_login.setPlaceholderText("Пароль")
        self.password_login.setEchoMode(QLineEdit.EchoMode.Password)

        # Глазик для логина
        self.password_login_action = QAction(self.icon_hide, "Показать пароль", self)
        self.password_login_action.setCheckable(True)
        self.password_login_action.toggled.connect(
            lambda checked: self._toggle_visibility(checked, self.password_login, self.password_login_action)
        )
        self.password_login.addAction(self.password_login_action, QLineEdit.ActionPosition.TrailingPosition)

        self.login_button = QPushButton("Войти")
        self.register_button = QPushButton("Зарегистрироваться")

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.login_button)
        button_layout.addWidget(self.register_button)

        layout.addWidget(self.login_login)
        layout.addWidget(self.password_login)
        layout.addLayout(button_layout)

        self.stack_layout.addWidget(self.login_view)

        self.login_button.clicked.connect(self._login_user_clicked)
        self.register_button.clicked.connect(lambda: self.stack_layout.setCurrentIndex(1))

        self.login_login.setValidator(username_validator)
        self.password_login.setValidator(password_validator)

    # ------------------- REGISTER VIEW -------------------
    def _setup_register_view(self, username_validator, password_validator, email_validator):
        self.register_view = QFrame()
        layout = QVBoxLayout()
        self.register_view.setLayout(layout)

        self.login_register = QLineEdit()
        self.login_register.setPlaceholderText("Придумайте логин")

        self.email_register = QLineEdit()
        self.email_register.setPlaceholderText("E-Mail")

        self.password_register = QLineEdit()
        self.password_register.setPlaceholderText("Пароль")
        self.password_register.setEchoMode(QLineEdit.EchoMode.Password)

        self.password_confirm = QLineEdit()
        self.password_confirm.setPlaceholderText("Повторите пароль")
        self.password_confirm.setEchoMode(QLineEdit.EchoMode.Password)

        # Глазики для регистрации
        self.password_register_action = QAction(self.icon_hide, "Показать пароль", self)
        self.password_register_action.setCheckable(True)
        self.password_register_action.toggled.connect(
            lambda checked: self._toggle_visibility(checked, self.password_register, self.password_register_action)
        )
        self.password_register.addAction(self.password_register_action, QLineEdit.ActionPosition.TrailingPosition)

        self.password_confirm_action = QAction(self.icon_hide, "Показать пароль", self)
        self.password_confirm_action.setCheckable(True)
        self.password_confirm_action.toggled.connect(
            lambda checked: self._toggle_visibility(checked, self.password_confirm, self.password_confirm_action)
        )
        self.password_confirm.addAction(self.password_confirm_action, QLineEdit.ActionPosition.TrailingPosition)

        self.register_register_button = QPushButton("Зарегистрироваться")
        self.already_registered_button = QPushButton("Уже зарегистрирован, войти")

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.register_register_button)
        button_layout.addWidget(self.already_registered_button)

        layout.addWidget(self.login_register)
        layout.addWidget(self.email_register)
        layout.addWidget(self.password_register)
        layout.addWidget(self.password_confirm)
        layout.addLayout(button_layout)

        self.stack_layout.addWidget(self.register_view)

        self.register_register_button.clicked.connect(self._register_user_clicked)
        self.already_registered_button.clicked.connect(lambda: self.stack_layout.setCurrentIndex(0))

        self.login_register.setValidator(username_validator)
        self.password_register.setValidator(password_validator)
        self.email_register.setValidator(email_validator)
        self.email_register.setMaxLength(60)

    # ------------------- PUBLIC -------------------
    def get_user(self) -> usr.User | None:
        """Возвращает объект User после успешного входа или регистрации."""
        return self._user

    # ------------------- PRIVATE -------------------
    def _toggle_visibility(self, checked: bool, line_edit: QLineEdit, action: QAction):
        if checked:
            line_edit.setEchoMode(QLineEdit.EchoMode.Normal)
            action.setIcon(self.icon_show)
        else:
            line_edit.setEchoMode(QLineEdit.EchoMode.Password)
            action.setIcon(self.icon_hide)

    def _login_user_clicked(self):
        user = self._login_user()
        if user:
            self._user = user
            self.accept()

    def _register_user_clicked(self):
        user = self._register_user()
        if user:
            self._user = user
            self.accept()

    def _login_user(self) -> usr.User | None:
        username = self.login_login.text().strip()
        password = self.password_login.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Ошибка", "Заполните имя пользователя и пароль!")
            return None

        conn = None
        try:
            config = connection.load_config()
            conn = connection.db_connect(config)
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT id_user, username, password_hash, role FROM spaces.users WHERE username = %s",
                    (username,)
                )
                result = cur.fetchone()
                if not result:
                    QMessageBox.warning(self, "Ошибка", "Неверное имя!")
                    return None

                user_id, nickname, password_hash, role = result
                if not bcrypt.checkpw(password.encode(), password_hash.encode()):
                    QMessageBox.warning(self, "Ошибка", "Неверный пароль!")
                    return None

                QMessageBox.information(self, "Успешно", f"Вход выполнен! Роль: {role}")
                return usr.User(id=user_id, nickname=nickname, role=role)

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"{e}")
            return None
        finally:
            if conn:
                conn.close()

    def _register_user(self) -> usr.User | None:
        username = self.login_register.text().strip()
        email = self.email_register.text().strip()
        password = self.password_register.text().strip()
        password_confirm = self.password_confirm.text().strip()

        if not username or not email or not password or not password_confirm:
            QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return None

        if password != password_confirm:
            QMessageBox.warning(self, "Ошибка", "Пароли не совпадают!")
            return None

        password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        user = usr.User(nickname=username, email=email, role="user", password_hash=password_hash)

        conn = None
        try:
            config = connection.load_config()
            conn = connection.db_connect(config)
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM spaces.users WHERE username = %s OR email = %s", (username, email))
                if cur.fetchone():
                    QMessageBox.warning(self, "Ошибка", "Имя или email заняты!")
                    return None

                user.insert(cur)
                conn.commit()

            QMessageBox.information(self, "Успешно", f"Регистрация прошла успешно! Ваш id: {user.id}")
            return user

        except Exception as e:
            if conn:
                conn.rollback()
            QMessageBox.critical(self, "Ошибка", f"{e}")
            return None
        finally:
            if conn:
                conn.close()