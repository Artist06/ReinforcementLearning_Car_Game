from enum import Enum

class Action(Enum):
    LEFT = 0
    RIGHT = 1
    DOWN = 2
    UP = 3
    UP_RIGHT = 4
    DOWN_RIGHT = 5
    UP_LEFT = 6
    DOWN_LEFT = 7
    IDLE = 8