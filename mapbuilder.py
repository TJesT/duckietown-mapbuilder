from dataclasses import dataclass
from typing import Tuple, overload
from os.path import expanduser
import png
import cv2
import numpy as np

@dataclass(init=True, repr=True, eq=True, frozen=True)
class Sign:
    type: str
    rotate: int
    x: float
    y: float

@dataclass(init=True, repr=True, eq=True, frozen=True)
class DuckieMap:
    tiles: Tuple[Tuple[str]]
    width: int
    height: int

class MapBuilder:
    _MAPS_PATH = '~/.local/lib/python3.8/site-packages/duckietown_world/data/gd1/maps'
    _MOVES = ((0, 1), (1, 0), (0, -1), (-1, 0))
    
    def _countNeighbors(bitmap: np.ndarray, x: int, y: int) -> int:
        width, height = bitmap.shape
        count = 0
        for dx, dy in MapBuilder._MOVES:
            if width > x + dx >= 0 \
                and height > y + dy >= 0 \
                and bitmap[x+dx][y+dy] == 255:
                    count += 1
        
        return count

    def _hasNeighbours(bitmap: np.ndarray, x: int, y: int) -> Tuple[bool]:
        width, height = bitmap.shape
        
        neighbour = [False, False, False, False]
        for i, (dx, dy) in enumerate(MapBuilder._MOVES):
            neighbour[i] = width > x + dx >= 0 \
                and height > y + dy >= 0       \
                and bitmap[x+dx][y+dy] == 255
                    
        return neighbour
        
    def _bitmap2duckie(bitmap: np.ndarray) -> DuckieMap:
        width, height = bitmap.shape
        
        neighbours_count = np.zeros((width, height))

        for i in range (0, width):
            for j in range (0, height):
                if bitmap[i][j] != 0:
                    neighbours_count[i][j] = MapBuilder._countNeighbors(bitmap, i, j)
                    
        tiles = [['' for i in range(width)] for j in range(height)]

        for i in range (0, width):
            for j in range (0, height):
                has_neighbour = MapBuilder._hasNeighbours(bitmap, i, j)

                if neighbours_count[i][j] == 0:
                    tiles[i][j] = 'floor'
                elif neighbours_count[i][j] == 1:
                    #TODO: logic for dead ends
                    pass
                elif neighbours_count[i][j] == 2:    
                    if has_neighbour[0] and has_neighbour[2]:
                        tiles[i][j] = 'straight/W'
                    elif has_neighbour[1] and has_neighbour[3]:
                        tiles[i][j] = 'straight/N'
                    elif has_neighbour[0] and has_neighbour[1]:
                        tiles[i][j] = 'curve_right/N'
                    elif has_neighbour[1] and has_neighbour[2]:
                        tiles[i][j] = 'curve_left/N'
                    elif has_neighbour[2] and has_neighbour[3]:
                        tiles[i][j] = 'curve_left/E'
                    elif has_neighbour[3] and has_neighbour[0]:
                        tiles[i][j] = 'curve_right/W'
                elif neighbours_count[i][j] == 3:
                    if not has_neighbour[0]:
                        tiles[i][j] = '3way_left/N'
                    elif not has_neighbour[1]:
                        tiles[i][j] = '3way_left/E'
                    elif not has_neighbour[2]:
                        tiles[i][j] = '3way_left/S'
                    elif not has_neighbour[3]:
                        tiles[i][j] = '3way_left/W'
                elif neighbours_count[i][j] == 4:
                    tiles[i][j] = '4way'
        
        return DuckieMap(tiles, width, height)
   

    def _duckie2signs(duckie: DuckieMap) -> Tuple[Sign]:
        tiles, w, h = duckie.tiles, duckie.width, duckie.height
        
        signs = []
        for i in range(0, w):
            for j in range (0, h):
                x1 = j+1
                y1 = i
                if tiles[i][j] == '3way_left/W':
                    signs.append(Sign('sign_T_intersect', 90, x1-0.5, y1-1.25))
                    signs.append(Sign('sign_left_T_intersect', 0, x1-0.25, y1-1.25))
                    signs.append(Sign('sign_right_T_intersect', 180, x1-1.25, y1+0.25))
                elif tiles[i][j] == '3way_left/S':
                    signs.append(Sign('sign_T_intersect', 0, x1-1.25, y1-0.5))
                    signs.append(Sign('sign_left_T_intersect', -90, x1-1.25, y1-0.75))
                    signs.append(Sign('sign_right_T_intersect', 90, x1+0.25, y1+0.25))
                elif tiles[i][j] == '3way_left/E':
                    signs.append(Sign('sign_T_intersect', -90, x1-0.5, y1+0.25))
                    signs.append(Sign('sign_left_T_intersect', 180, x1-0.75, y1+0.25))
                    signs.append(Sign('sign_right_T_intersect', 0, x1+0.25, y1-1.25))
                elif tiles[i][j] == '3way_left/N':
                    signs.append(Sign('sign_T_intersect', 180, x1+0.25, y1-0.5))
                    signs.append(Sign('sign_left_T_intersect', 90, x1+0.25, y1-0.25))
                    signs.append(Sign('sign_right_T_intersect', -90, x1-1.25, y1-1.25))
                elif tiles[i][j] == '4way':
                    signs.append(Sign('sign_4_way_intersect', 180, x1-1.25, y1+0.25))
                    signs.append(Sign('sign_4_way_intersect', 90, x1+0.25, y1+0.25))
                    signs.append(Sign('sign_4_way_intersect', -90, x1-1.25, y1-1.25))
                    signs.append(Sign('sign_4_way_intersect', 0, x1+0.25, y1-1.25))
        
        return signs

    def _saveMap(file_name: str, duckie: DuckieMap, signs: Tuple[Sign]):
        tiles = duckie.tiles

        with open(file_name, 'w') as file_map:
            file_map.write('tiles:\n')

            for tile_line in tiles:
                file_map.write('  - [')
                file_map.write(', '.join(tile_line))
                file_map.write(']\n')
            
            file_map.write('objects:' + '\n')
            
            for i, sign in enumerate(signs, 1):
                file_map.write(
                    f' sign{i}:\n'
                    f'  kind: {sign.type}\n'
                    f'  pos: [{sign.x}, {sign.y}]\n'
                    f'  rotate: {sign.rotate}\n'
                    f'  height: 0.3\n'
                )
            
            file_map.write('tile_size: 0.585')
    
    def parse(map_name: str, bitmap: np.ndarray, *, inject=False):
        duckie = MapBuilder._bitmap2duckie(bitmap)
        signs  = MapBuilder._duckie2signs(duckie)
        
        if inject:
            map_name = expanduser(f'{MapBuilder._MAPS_PATH}/{map_name}.yaml')
        else:
            map_name = f'{map_name}.txt'

        MapBuilder._saveMap(map_name, duckie, signs)

if __name__ == '__main__':
    map_name = 'map1'
    S = 600 #высота экрана
    h = 10  #высота
    w = 10  #ширина

    mult = min(S//h, S//w)
    h1 = h*mult
    w1 = w*mult

    def paint(event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            if nul[y//mult][x//mult] == 0:
                nul[y//mult][x//mult] = 255
            else:
                nul[y//mult][x//mult] = 0
    
    nul = np.zeros((h, w))
    cv2.namedWindow(map_name)
    cv2.setMouseCallback(map_name, paint)
    while True:
        img = cv2.resize(nul, (w1, h1), interpolation=cv2.INTER_AREA)
        cv2.imshow(map_name, img)
        if cv2.waitKey(20) & 0xFF == 27:
            break
    
    png.from_array(nul.astype(int).tolist(), 'L').save(f'{map_name}.png')

    MapBuilder.parse(map_name, nul, inject=True)
