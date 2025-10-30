from dataclasses import dataclass


@dataclass
class User:
    id: int = None
    nickname: str = ""
    name: str = ""
    surname: str = ""
    email: str = ""
    role: str = "user"
    password_hash: str = ""  # временно для вставки/проверки

    def insert(self, cursor):
        query = """
            INSERT INTO spaces.users (username, email, password_hash, role)
            VALUES (%s, %s, %s, %s)
            RETURNING id_user;
        """
        values = (self.nickname, self.email, self.password_hash, self.role)
        cursor.execute(query, values)
        self.id = cursor.fetchone()[0]

    def update(self, cursor):
        if self.id is None:
            raise ValueError("id отсутствует")
        query = """
            UPDATE spaces.users
            SET username = %s, email = %s, role = %s
            WHERE id_user = %s
        """
        values = (self.nickname, self.email, self.role, self.id)
        cursor.execute(query, values)