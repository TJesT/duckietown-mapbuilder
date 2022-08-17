from abc import ABC, abstractmethod
from copy import deepcopy
from typing import Protocol, Tuple, overload
from dataclasses import dataclass, field
from enum import Enum
from numpy.linalg import norm
import numpy as np

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
        cy = y + 0.5
        dx = 0.5
        dy = 0.5
        h  = 0.4
        return DuckieObject('sign_T_intersect',        90, cx, cy-dy, 0.2), \
                DuckieObject('sign_left_T_intersect',    0, cx+dx-h, cy-dy, 0.2), \
                DuckieObject('sign_right_T_intersect', 180, cx-dx+h, cy-dy, 0.2)
    def getSignsFor3wayS(x, y):
        cx = x + 0.5
        cy = y + 0.5
        dx = 0.5
        dy = 0.5
        h  = 0.4
        return DuckieObject('sign_T_intersect',        0, cx-dx, cy, 0.2),  \
                DuckieObject('sign_left_T_intersect',  -90, cx-dx, cy-dy+h, 0.2), \
                DuckieObject('sign_right_T_intersect',  90, cx-dx, cy+dy-h, 0.2)
    def getSignsFor3wayE(x, y):
        cx = x + 0.5
        cy = y + 0.5
        dx = 0.5
        dy = 0.5
        h  = 0.4
        return DuckieObject('sign_T_intersect',      -90, cx, cy+dy, 0.2), \
                DuckieObject('sign_left_T_intersect', 180, cx-dx+h, cy+dy, 0.2), \
                DuckieObject('sign_right_T_intersect',  0, cx+dx-h, cy+dy, 0.2)
    def getSignsFor3wayN(x, y):
        cx = x + 0.5
        cy = y + 0.5
        dx = 0.5
        dy = 0.5
        h  = 0.4
        return DuckieObject('sign_T_intersect',       180, cx+dx, cy, 0.2), \
                DuckieObject('sign_left_T_intersect',   90, cx+dx, cy+dy-h, 0.2), \
                DuckieObject('sign_right_T_intersect', -90, cx+dx, cy-dy+h, 0.2)
    def getSignsFor4way(x, y):
        cx = x + 0.5
        cy = y + 0.5
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


@dataclass(init=True)
class MathematicalArea(ABC):
    __inverted: bool = field(default=False, init=False)

    def isInverted(self):
        return self.__inverted

    def __invert__(self):
        new = deepcopy(self)
        new.__inverted ^= True
        return new
    
    def __contains__(self, item: tuple[float, float]) -> bool:
        return self.isInverted() ^ self._contains(item)

    @abstractmethod
    def _contains(self, item: tuple[float, float]) -> bool:
        ...
        

@dataclass(init=True, repr=True, eq=True)
class RectArea(MathematicalArea):
    x_min: float = 0.0
    x_max: float = 0.0
    y_min: float = 0.0
    y_max: float = 0.0

    def __post_init(self):
        self.x_min -= 0.00001
        self.x_max += 0.00001
        self.y_min -= 0.00001
        self.y_max += 0.00001
    def _contains(self, item: tuple[float, float]) -> bool:
        return self.x_min <= item[0] <= self.x_max \
            and self.y_min <= item[1] <= self.y_max


@dataclass(init=True, repr=True, eq=True)
class SectArea(MathematicalArea):
    x_center:  float = 0.0
    y_center:  float = 0.0
    r:         float = 0.0
    theta_min: float = 0.0
    theta_max: float = 0.0

    def __post_init__(self):
        self.theta_min %= 2*np.pi
        self.theta_max %= 2*np.pi
        self.r = 0.0 if self.r <= 0.0 else self.r

    def _contains(self, item: tuple[float, float]) -> bool:
        dr = np.array(item) - np.array((self.x_center, self.y_center))
        d = norm(dr)

        if d <= 0: return True

        # phi = np.arccos(np.clip(np.dot(dr / d, np.array([1.0, 0.0])), -1.0, 1.0))
        phi = np.arctan2(*dr)

        # print(self.x_center, self.y_center) if d <= self.r else None

        # print("phi", phi*180/np.pi) if d <= self.r else None

        angle_view = self.theta_max - self.theta_min + 2*np.pi
        angle_view %= 2*np.pi

        # print("angle_view", angle_view * 180 / np.pi) if d <= self.r else None

        angle_face = self.theta_min + angle_view / 2
        angle_face %= 2*np.pi

        # print("angle_face", angle_face * 180 / np.pi) if d <= self.r else None

        angle_diff = (angle_face - phi + np.pi + 2*np.pi) % (2*np.pi) - np.pi

        # print("angle_diff", angle_diff * 180 / np.pi) if d <= self.r else None

        # print(-angle_view/2 <= angle_diff <= angle_view/2) if d <= self.r else None

        return d <= self.r and -angle_view/2 <= angle_diff <= angle_view/2

@dataclass(init=True, repr=True, eq=True)
class ComplexArea(MathematicalArea):
    __consists_of: list[MathematicalArea] = field(default_factory=list, init=False)

    def __init__(self, *areas: MathematicalArea):
        self.__consists_of = list(areas)

    def append(self, area: MathematicalArea):
        self.__consists_of.append(area)

    def get(self, i):
        return self.__consists_of[i]

    def _contains(self, item: tuple[float, float]):
        positive = []
        negative = []

        for area in self.__consists_of:
            if area.isInverted():
                negative.append(area)
            else:
                positive.append(area)

        return any(item in area for area in positive) \
            and all(item in area for area in negative)

def get_duckietile_area(sign: str) -> ComplexArea:
    return {'floor': lambda _, __: ComplexArea(),
        'straight/W': lambda cx, cy: RectArea(cx - 0.425, cx + 0.425, cy - 0.5, cy + 0.5),
        'straight/N': lambda cx, cy: RectArea(cx - 0.5, cx + 0.5, cy - 0.425, cy + 0.425),
        'curve_left/N': lambda cx, cy: ComplexArea(
            SectArea(cx + 0.5, cy - 0.5, 0.925, 3/2*np.pi, 2*np.pi - 0.00001),
            ~SectArea(cx + 0.5, cy - 0.5, 0.075, 3/2*np.pi, 2*np.pi - 0.00001),
        ),
        'curve_left/E': lambda cx, cy: ComplexArea(
            SectArea(cx - 0.5, cy - 0.5, 0.925, 0, 1/2*np.pi),
            ~SectArea(cx - 0.5, cy - 0.5, 0.075, 0, 1/2*np.pi)
        ),
        'curve_left/S': lambda cx, cy: ComplexArea(
            SectArea(cx - 0.5, cy + 0.5, 0.925, np.pi/2, np.pi),
            ~SectArea(cx - 0.5, cy + 0.5, 0.075, np.pi/2, np.pi),
        ),
        'curve_left/W': lambda cx, cy: ComplexArea(
            SectArea(cx + 0.5, cy + 0.5, 0.925, np.pi, 3/2*np.pi),
            ~SectArea(cx + 0.5, cy + 0.5, 0.075, np.pi, 3/2*np.pi)
        ),
        '3way_left/W': lambda cx, cy: ComplexArea(
            RectArea(cx - 0.425, cx + 0.5, cy - 0.425, cy + 0.425),
            RectArea(cx - 0.425, cx + 0.425, cy - 0.5, cy + 0.5)
        ),
        '3way_left/S': lambda cx, cy: ComplexArea(
            RectArea(cx - 0.5, cx + 0.5, cy - 0.425, cy + 0.425),
            RectArea(cx - 0.425, cx + 0.425, cy - 0.425, cy + 0.5)
        ),
        '3way_left/E': lambda cx, cy: ComplexArea(
            RectArea(cx - 0.5, cx + 0.425, cy - 0.425, cy + 0.425),
            RectArea(cx - 0.425, cx + 0.425, cy - 0.5, cy + 0.5)
        ),
        '3way_left/N': lambda cx, cy: ComplexArea(
            RectArea(cx - 0.5, cx + 0.5, cy - 0.425, cy + 0.425),
            RectArea(cx - 0.425, cx + 0.425, cy - 0.5, cy + 0.425)
        ),
        '4way': lambda cx, cy: ComplexArea(
            RectArea(cx - 0.5, cx + 0.5, cy - 0.425, cy + 0.425),
            RectArea(cx - 0.425, cx + 0.425, cy - 0.5, cy + 0.5)
        )}[sign]

if __name__ == '__main__':
    point = (0.5, 0.5)

    print(point in get_duckietile_area('curve_left/N')(0.5, 0.5))

    
