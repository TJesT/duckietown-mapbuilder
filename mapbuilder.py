from dataclasses import dataclass
from typing import Tuple
from os.path import expanduser
import numpy as np

@dataclass(init=True, repr=True, eq=True, frozen=True)
class _Sign:
    type: str
    rotate: int
    x: float
    y: float

@dataclass(init=True, repr=True, eq=True, frozen=True)
class _DuckieMap:
    tiles: Tuple[Tuple[str]]
    width: int
    height: int

def _getTilesFor3wayW(x, y):
    return _Sign('sign_T_intersect',        90, x-0.50, y-1.25), \
            _Sign('sign_left_T_intersect',    0, x-0.25, y-1.25), \
            _Sign('sign_right_T_intersect', 180, x-1.25, y+0.25)
def _getTilesFor3wayS(x, y):
    return _Sign('sign_T_intersect',        0, x-1.25, y-0.5),  \
            _Sign('sign_left_T_intersect', -90, x-1.25, y-0.75), \
            _Sign('sign_right_T_intersect', 90, x+0.25, y+0.25)
def _getTilesFor3wayE(x, y):
    return _Sign('sign_T_intersect',      -90, x-0.50, y+0.25), \
            _Sign('sign_left_T_intersect', 180, x-0.75, y+0.25), \
            _Sign('sign_right_T_intersect',  0, x+0.25, y-1.25)
def _getTilesFor3wayN(x, y):
    return _Sign('sign_T_intersect',       180, x+0.25, y-0.50), \
            _Sign('sign_left_T_intersect',   90, x+0.25, y-0.25), \
            _Sign('sign_right_T_intersect', -90, x-1.25, y-1.25)
def _getTilesFor4way(x, y):
    return _Sign('sign_4_way_intersect', 180, x-1.25, y+0.25), \
            _Sign('sign_4_way_intersect',  90, x+0.25, y+0.25), \
            _Sign('sign_4_way_intersect', -90, x-1.25, y-1.25), \
            _Sign('sign_4_way_intersect',   0, x+0.25, y-1.25)

class MapBuilder:
    _MAPS_PATH = '~/.local/lib/python3.8/site-packages/duckietown_world/data/gd1/maps'
    _MOVES = ((0, 1), (1, 0), (0, -1), (-1, 0))
    _TILES = {0 : {(False, False, False, False):'floor'},
             1 : {(True,  False, False, False):'straight/W', 
                  (False, True,  False, False):'straight/N',
                  (False, False, True,  False):'straight/W',
                  (False, False, False, True): 'straight/N'},
             2 : {(True,  False, True,  False):'straight/W',
                  (False, True,  False, True): 'straight/N',
                  (True,  True,  False, False):'curve_right/N',
                  (False, True,  True,  False):'curve_left/N',
                  (False, False, True,  True): 'curve_left/E',
                  (True,  False, False, True): 'curve_right/W'},
             3 : {(False, True,  True,  True): '3way_left/N',
                  (True,  False, True,  True): '3way_left/E',
                  (True,  True,  False, True): '3way_left/S',
                  (True,  True,  True,  False):'3way_left/W'},
             4 : {(True,  True,  True,  True): '4way'}}
    _SIGNS = {'3way_left/W': _getTilesFor3wayW,
             '3way_left/S':  _getTilesFor3wayS,
             '3way_left/E':  _getTilesFor3wayE,
             '3way_left/N':  _getTilesFor3wayN,
             '4way':         _getTilesFor4way}

    
    def _countNeighbors(bitmap: np.ndarray, x: int, y: int) -> int:
        width, height = bitmap.shape
        count = 0
        for dx, dy in MapBuilder._MOVES:
            if width > x + dx >= 0       \
                and height > y + dy >= 0 \
                and bitmap[x+dx][y+dy] == 255:
                count += 1
        
        return count

    def _hasNeighbours(bitmap: np.ndarray, x: int, y: int) -> Tuple[bool]:
        """if (x + dx_n, y + dy_n) has neigbour, then neighbour[n] is True"""
        if bitmap[x][y] == 0:
            return False, False, False, False

        width, height = bitmap.shape
        
        neighbour = [False, False, False, False]
        
        for i, (dx, dy) in enumerate(MapBuilder._MOVES):
            neighbour[i] = width > x + dx >= 0 \
                and height > y + dy >= 0       \
                and bitmap[x+dx][y+dy] == 255
        print(f'{x=}, {y=}')            
        return tuple(neighbour)

    def _bitmap2duckie(bitmap: np.ndarray) -> _DuckieMap:
        """Make Duckietown Map from bitmap"""

        width, height = bitmap.shape
        
        neighbours_count = np.zeros((width, height))

        for i in range (0, width):
            for j in range (0, height):
                if bitmap[i][j] != 0:
                    neighbours_count[i][j] = MapBuilder._countNeighbors(bitmap, i, j)
                    
        tiles = [['floor' for i in range(height)] for j in range(width)]

        for i in range (0, width):
            for j in range (0, height):
                has_neighbour = MapBuilder._hasNeighbours(bitmap, i, j)
                
                COUNT     = neighbours_count[i][j]
                NEIGHBOURS = has_neighbour
                
                tiles[i][j] = MapBuilder._TILES[COUNT][NEIGHBOURS]
        
        return _DuckieMap(tiles, width, height)
   

    def _duckie2signs(duckie: _DuckieMap) -> Tuple[_Sign]:
        """Make sequence of Signs based on a Duckietown Map"""

        tiles, w, h = duckie.tiles, duckie.width, duckie.height
        
        signs = []
        for i in range(0, w):
            for j in range (0, h):
                x = j+1
                y = i
                TILE = tiles[i][j]

                if TILE in MapBuilder._SIGNS.keys():
                    signs.extend( MapBuilder._SIGNS[TILE](x, y) )
                
        return signs

    def _saveMap(file_name: str, duckie: _DuckieMap, signs: Tuple[_Sign]):
        """Generates valid Duckietown map and saves it"""

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
        """Parses bitmap and writes it file"""

        duckie = MapBuilder._bitmap2duckie(bitmap)
        signs  = MapBuilder._duckie2signs(duckie)
        
        if inject:
            map_name = expanduser(f'{MapBuilder._MAPS_PATH}/{map_name}.yaml')
        else:
            map_name = f'{map_name}.txt'

        MapBuilder._saveMap(map_name, duckie, signs)

