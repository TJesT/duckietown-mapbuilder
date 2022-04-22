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

class MapBuilder:
    _MAPS_PATH = '~/.local/lib/python3.8/site-packages/duckietown_world/data/gd1/maps'
    _MOVES = ((0, 1), (1, 0), (0, -1), (-1, 0))

    def _countNeighbors(bitmap: np.ndarray, x: int, y: int) -> int:
        width, height = bitmap.shape
        count = 0
        for dx, dy in MapBuilder._MOVES:
            if width > x + dx >= 0      \
                and height > y + dy >= 0 \
                and bitmap[x+dx][y+dy] == 255:
                count += 1
        
        return count

    def _hasNeighbours(bitmap: np.ndarray, x: int, y: int) -> Tuple[bool]:
        """if (x + dx_n, y + dy_n) has neigbour, then neighbour[n] is True"""
        
        width, height = bitmap.shape
        
        neighbour = [False, False, False, False]
        for i, (dx, dy) in enumerate(MapBuilder._MOVES):
            neighbour[i] = width > x + dx >= 0 \
                and height > y + dy >= 0        \
                and bitmap[x+dx][y+dy] == 255
                    
        return neighbour

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

                #TODO: replace all if-statements with mapping:
                ## tiles[i][j] = DICT[COUNT][NEIGHBOURS]
                ## - DICT      = mapping dicionary
                ## - COUNT     = neighbours_count[i][j]
                ## - NEGHBOURS = has_neighbour

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
        
        return _DuckieMap(tiles, width, height)
   

    def _duckie2signs(duckie: _DuckieMap) -> Tuple[_Sign]:
        """Make sequence of Signs based on a Duckietown Map"""

        tiles, w, h = duckie.tiles, duckie.width, duckie.height
        
        signs = []
        for i in range(0, w):
            for j in range (0, h):
                x1 = j+1
                y1 = i

                #TODO: replace all if-statements with mapping:
                ## signs.extend( DICT[TILE](x, y) )
                ## - DICT      = mapping dicionary
                ###  DICT[TILE] -> _Sign.__init__
                #### lambda x, y: (_Sign('type1',   0, x+1, y+1), 
                ####               _Sign('type2',  90, x-1, y+1),
                ####               _Sign('type3', -90, x+1, y-1))
                ## - TILE      = tiles[i][j]

                if tiles[i][j] == '3way_left/W':
                    signs.append(_Sign('sign_T_intersect',        90, x1-0.50, y1-1.25))
                    signs.append(_Sign('sign_left_T_intersect',    0, x1-0.25, y1-1.25))
                    signs.append(_Sign('sign_right_T_intersect', 180, x1-1.25, y1+0.25))
                elif tiles[i][j] == '3way_left/S':
                    signs.append(_Sign('sign_T_intersect',        0, x1-1.25, y1-0.5))
                    signs.append(_Sign('sign_left_T_intersect', -90, x1-1.25, y1-0.75))
                    signs.append(_Sign('sign_right_T_intersect', 90, x1+0.25, y1+0.25))
                elif tiles[i][j] == '3way_left/E':
                    signs.append(_Sign('sign_T_intersect',      -90, x1-0.50, y1+0.25))
                    signs.append(_Sign('sign_left_T_intersect', 180, x1-0.75, y1+0.25))
                    signs.append(_Sign('sign_right_T_intersect',  0, x1+0.25, y1-1.25))
                elif tiles[i][j] == '3way_left/N':
                    signs.append(_Sign('sign_T_intersect',       180, x1+0.25, y1-0.50))
                    signs.append(_Sign('sign_left_T_intersect',   90, x1+0.25, y1-0.25))
                    signs.append(_Sign('sign_right_T_intersect', -90, x1-1.25, y1-1.25))
                elif tiles[i][j] == '4way':
                    signs.append(_Sign('sign_4_way_intersect', 180, x1-1.25, y1+0.25))
                    signs.append(_Sign('sign_4_way_intersect',  90, x1+0.25, y1+0.25))
                    signs.append(_Sign('sign_4_way_intersect', -90, x1-1.25, y1-1.25))
                    signs.append(_Sign('sign_4_way_intersect',   0, x1+0.25, y1-1.25))
        
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

