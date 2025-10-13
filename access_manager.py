import inspect
import connect_DB as connection
import track_object_state as track_state
from space import Space


class AccessManager:
    def __init__(self, user):
        self.user = user

    def _get_caller_name(self):
        """Возвращает имя функции, которая вызвала текущий метод."""
        stack = inspect.stack()
        if len(stack) > 2:
            # stack[1] — текущая функция (_get_caller_name)
            # stack[2] — функция, которая вызвала этот метод
            return stack[2].function
        return "unknown"

    def can_edit(self, space: Space) -> bool:
        """Проверяет, может ли пользователь редактировать указанное пространство."""
        caller = self._get_caller_name()
        print(f"[DEBUG] can_edit() вызван из функции: {caller}")

        # 1. Глобальная роль администратора
        if self.user.role == "admin":
            return True

        # 2. Новые или несохранённые пространства (созданы в текущей сессии)
        if getattr(space, "state", None) == track_state.ObjectState.NEW or getattr(space, "id_space", None) is None:
            return True

        # 3. Проверка по БД
        print(f"user_role_from_db, can_edit: {self.get_user_role_from_db(space.id_space)}")
        return self.get_user_role_from_db(space.id_space) == "editor"

    def can_view(self, space: Space) -> bool:
        """Проверяет, может ли пользователь просматривать указанное пространство."""
        caller = self._get_caller_name()
        print(f"[DEBUG] can_view() вызван из функции: {caller}")

        # 1. Администратор может всё
        if self.user.role == "admin":
            return True

        # 2. Новые или несохранённые пространства — можно видеть
        if getattr(space, "state", None) == track_state.ObjectState.NEW or getattr(space, "id_space", None) is None:
            return True

        # 3. Проверка по БД
        print(f"user_role_from_db, can_view: {self.get_user_role_from_db(space.id_space)}")
        return self.get_user_role_from_db(space.id_space) in ("editor", "viewer")

    def get_user_role_from_db(self, id_space: int) -> str | None:
        """Возвращает роль пользователя в указанном пространстве из БД."""
        if not id_space:
            return None

        config = connection.load_config()
        conn = connection.db_connect(config)
        try:
            with conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT role
                        FROM spaces.user_access
                        WHERE id_user = %s AND id_space = %s
                        """,
                        (self.user.id, id_space)
                    )
                    result = cursor.fetchone()
                    return result[0] if result else None
        finally:
            conn.close()

        # load_parent_space_from_DB:
            # Пользователь может его посмотреть, если он admin, editor, viewer. Просто user не может посмотреть
        # load_space_from_db_by_selection_from_spaces_list
            # Выводим список только тех пространств, где пользователь editor и viewer, для admin все пространства
        # show_full_structure_of_space
            # если пространство не NEW, то показываю всё, где пользователь editor и viewer (для admin всё показываю). Если есть пространства в дереве структуры,
            # где просто user, то в структуре заменить имя пространства на "скрыто для Вас" и не показывать вещи этого пространства в структуре.
        # show_thing_information
            # так как вещи в пространствах, где пользователь не является admin, editor или viewer не будут показаны, то автоматически пользователю можно посмотреть информацию
            # о тех вещах, которые он видит
        # show_space_information
            # для admin, editor и viewer
        # show_all_things_in_space
            # для admin, editor и viewer
        # load_space_from_DB
            # ПОСМОТРЕТЬ, ЕСТЬ ЛИ "ПРЯМЫЕ" ВЫЗОВЫ ИЛИ ТОЛЬКО КОСВЕННЫЕ ЧЕРЕЗ ФУНКЦИИ, ГДЕ УЖЕ ЕСТЬ ПРОВЕРКА ПРАВ
        # open_subspace_as_space
            # Пользователь может его посмотреть, если он admin, editor, viewer. Просто user не может посмотреть
        # save_space_to_DB
            # может admin и editor, viewer не может
        # delete_space
            # может admin и editor, viewer не может
        # delete_subspace
            # может admin и editor, viewer не может
        # delete_thing
            # может admin и editor, viewer не может
        # delete_all_subprojections
            # может admin и editor, viewer не может
        # delete_one_subprojection
            # может admin и editor, viewer не может
        # delete_mini_projection
            # может admin и editor, viewer не может
        # save_or_update_mini_projection
            # может admin и editor, viewer не может
        # add_new_space_projection
            # может admin и editor, viewer не может
        # delete_image
            # может admin и editor, viewer не может
        # add_image_of_space
            # может admin и editor, viewer не может
        # add_thing
            # может admin и editor, viewer не может
        # add_thing_projection
            # может admin и editor, viewer не может
        # add_subspace_projection
            # может admin и editor, viewer не может
        # add_subspace
            # может admin и editor, viewer не может
        # add_space_projection
            # может admin и editor, viewer не может
        # add_space
            # может admin и editor, viewer не может
        # create_new_space
            # может любой пользователь
        # find_thing
            # может любой пользователь. Поиск будет происходить для admin во всех пространствах.
            # Для user в тех пространствах, где он editor или viewer