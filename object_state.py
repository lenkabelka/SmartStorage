from enum import auto, Enum

class State(Enum):
    NEW = auto() # 1
    UNMODIFIED = auto() # 2
    MODIFIED = auto() # 3
    DELETED = auto() # 4