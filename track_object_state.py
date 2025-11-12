from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Set, Dict, Any
from abc import ABC, abstractmethod


class ObjectState(Enum):
    NEW = auto()
    UNMODIFIED = auto()
    MODIFIED = auto()
    DELETED = auto()


@dataclass
class Trackable(ABC):
    _state: Optional[ObjectState] = field(default=ObjectState.UNMODIFIED, init=False, repr=False)
    _db_fields: Set[str] = field(default_factory=set, init=False, repr=False)
    _non_db_fields: Set[str] = field(default_factory=set, init=False, repr=False)
    _original_values: Dict[str, Any] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self):
        # Сохраняю оригинальные значения для отслеживания изменений
        self._original_values = {f: getattr(self, f) for f in self._db_fields}

    def __setattr__(self, key, value):
        # Если ключ - отслеживаемое поле из БД
        if hasattr(self, '_db_fields') and key in self._db_fields:
            current_value = getattr(self, key, None)
            if current_value != value:
                super().__setattr__(key, value)
                if hasattr(self, '_state'):
                    # Меняю состояние, если объект не NEW и не DELETED
                    if self._state == ObjectState.UNMODIFIED:
                        print(f"[DEBUG] → Состояние изменено на MODIFIED для ❌❌❌❌❌❌❌❌❌❌❌ {self}")
                        self._state = ObjectState.MODIFIED
                return
        super().__setattr__(key, value)

    @property
    def state(self) -> Optional[ObjectState]:
        return self._state

    def mark_new(self):
        self._state = ObjectState.NEW

    def mark_deleted(self):
        if self._state == ObjectState.NEW:
            # Новый объект - можно просто не сохранять
            self._state = None
        elif self._state != ObjectState.DELETED:
            self._state = ObjectState.DELETED

    def reset_state(self):
        self._state = ObjectState.UNMODIFIED
        self._original_values = {f: getattr(self, f) for f in self._db_fields}

    def set_state(self, state_to_set):
        self._state = state_to_set

    def save(self, cursor):
        match self._state:
            case ObjectState.NEW:
                self.insert(cursor)
            case ObjectState.MODIFIED:
                self.update(cursor)
            case ObjectState.DELETED:
                self.delete(cursor)
            case ObjectState.UNMODIFIED | None:
                pass  # ничего не делать

    @abstractmethod
    def insert(self, cursor):
        pass

    @abstractmethod
    def update(self, cursor):
        pass

    @abstractmethod
    def delete(self, cursor):
        pass





# NEW → объект создан в коде, ещё не сохранён в БД.
# Меняю поля — остаётся NEW.
#
# UNMODIFIED → загружен из БД, ничего не менялось.
# Меняю поля — становится MODIFIED.
#
# MODIFIED → загружен из БД и изменён.
#
# DELETED → помечен на удаление.