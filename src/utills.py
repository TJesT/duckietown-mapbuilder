from typing import Tuple
from dataclasses import dataclass
from enum import Enum, auto

class Direction(Enum):
    DOWN  = 0
    RIGHT = 1
    UP    = 2
    LEFT  = 3
    
    def neighbors(location: tuple[int, int], height: int, width: int):
        res = []
        x, y = location
        if x != 0:
            res.append((Direction.UP, x-1, y))
        if y != 0:
            res.append((Direction.LEFT, x, y-1))
        if x < height - 1:
            res.append((Direction.DOWN, x+1, y))
        if y < width - 1:
            res.append((Direction.RIGHT, x, y+1))
        return res

    def reverse(self):
        return {Direction.RIGHT: Direction.LEFT,
                Direction.LEFT: Direction.RIGHT,
                Direction.UP: Direction.DOWN,
                Direction.DOWN: Direction.UP}[self]

@dataclass(init=True, repr=True, eq=True, frozen=True)
class DuckieObject:
    type: str
    rotate: int
    x: float
    y: float
    height: float

    def toGym(self, name: str) -> str:
        return f' {name}:\n'                         + \
                f'  kind: {self.type}\n'              + \
                f'  pos: [{self.x:.2}, {self.y:.2}]\n' + \
                f'  rotate: {self.rotate}\n'            + \
                f'  height: {self.height:.2}\n'

    def getSignsFor3wayW(x, y):
        cx = x + 0.5
        cy = y - 0.5
        dx = 0.5
        dy = 0.5
        h  = 0.4
        return DuckieObject('sign_T_intersect',        90, cx, cy-dy, 0.2), \
                DuckieObject('sign_left_T_intersect',    0, cx+dx-h, cy-dy, 0.2), \
                DuckieObject('sign_right_T_intersect', 180, cx-dx+h, cy-dy, 0.2)
    def getSignsFor3wayS(x, y):
        cx = x + 0.5
        cy = y - 0.5
        dx = 0.5
        dy = 0.5
        h  = 0.4
        return DuckieObject('sign_T_intersect',        0, cx-dx, cy, 0.2),  \
                DuckieObject('sign_left_T_intersect',  -90, cx-dx, cy-dy+h, 0.2), \
                DuckieObject('sign_right_T_intersect',  90, cx-dx, cy+dy-h, 0.2)
    def getSignsFor3wayE(x, y):
        cx = x + 0.5
        cy = y - 0.5
        dx = 0.5
        dy = 0.5
        h  = 0.4
        return DuckieObject('sign_T_intersect',      -90, cx, cy+dy, 0.2), \
                DuckieObject('sign_left_T_intersect', 180, cx-dx+h, cy+dy, 0.2), \
                DuckieObject('sign_right_T_intersect',  0, cx+dx-h, cy+dy, 0.2)
    def getSignsFor3wayN(x, y):
        cx = x + 0.5
        cy = y - 0.5
        dx = 0.5
        dy = 0.5
        h  = 0.4
        return DuckieObject('sign_T_intersect',       180, cx+dx, cy, 0.2), \
                DuckieObject('sign_left_T_intersect',   90, cx+dx, cy+dy-h, 0.2), \
                DuckieObject('sign_right_T_intersect', -90, cx+dx, cy-dy+h, 0.2)
    def getSignsFor4way(x, y):
        cx = x + 0.5
        cy = y - 0.5
        dx = 0.5
        dy = 0.5
        return DuckieObject('sign_4_way_intersect',   0, cx-dx, cy+dy, 0.2), \
                DuckieObject('sign_4_way_intersect', -90, cx+dx, cy+dy, 0.2), \
                DuckieObject('sign_4_way_intersect',  90, cx-dx, cy-dy, 0.2),  \
                DuckieObject('sign_4_way_intersect', 180, cx+dx, cy-dy, 0.2)

@dataclass(init=True, repr=True, eq=True, frozen=True)
class DuckieMap:
    tiles: Tuple[Tuple[str]]
    width: int
    height: int

@dataclass(init=True, repr=True, eq=True, frozen=True)
class DuckieBHeight:
    min: float
    max: float
    
    @property
    def dh(self):
        return self.max - self.min

if __name__ == '__main__':
    s = DuckieBHeight(0.3, 0.5)