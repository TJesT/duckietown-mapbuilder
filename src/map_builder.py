from bridson import poisson_disc_samples as pds
from utills import *
from typing import Tuple
from os.path import expanduser
import numpy as np
import random

import cv2

from map_generator import MapGenerator

class MapBuilder:
    _MAPS_PATH = '~/.local/lib/python3.8/site-packages/duckietown_world/data/gd1/maps'
    _TILE = {0 : {(False, False, False, False):'floor'},
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
    _SIGNS = {'3way_left/W': DuckieObject.getSignsFor3wayW,
             '3way_left/S':  DuckieObject.getSignsFor3wayS,
             '3way_left/E':  DuckieObject.getSignsFor3wayE,
             '3way_left/N':  DuckieObject.getSignsFor3wayN,
             '4way':         DuckieObject.getSignsFor4way}

    def _countNeighbors(bitmap: np.ndarray, x: int, y: int) -> int:
        width, height = bitmap.shape
        count = 0

        moves = ((0, 1), (1, 0), (0, -1), (-1, 0))

        for dx, dy in moves:
            if width > x + dx >= 0      \
                and height > y + dy >= 0 \
                and bitmap[x+dx][y+dy] == 255:
                count += 1
        
        return count

    def _hasNeighbours(bitmap: np.ndarray, x: int, y: int) -> Tuple[bool]:
        """if (x + dx_n, y + dy_n) has neigbour, then neighbour[n] is True"""
        if bitmap[x][y] == 0:
            return (False,) * 4

        width, height = bitmap.shape
        moves = ((0, 1), (1, 0), (0, -1), (-1, 0))
        
        neighbour = [False, ] * 4
        
        for i, (dx, dy) in enumerate(moves):
            neighbour[i] = width > x + dx >= 0 \
                and height > y + dy >= 0        \
                and bitmap[x+dx][y+dy] == 255
          
        return tuple(neighbour)

    def _bitmap2duckie(bitmap: np.ndarray) -> DuckieMap:
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
                
                tiles[i][j] = MapBuilder._TILE[COUNT][NEIGHBOURS]
        
        return DuckieMap(tiles, width, height)
   
    def _duckie2signs(duckie: DuckieMap) -> Tuple[DuckieObject]:
        """Make sequence of Signs based on a Duckietown Map"""

        tiles, w, h = duckie.tiles, duckie.width, duckie.height
        
        signs = []
        
        for i in range(w):
            for j in range (h):
                x = j
                y = i - w + h - 1
                tile = tiles[i][j]

                if tile in MapBuilder._SIGNS.keys():
                    signs.extend( MapBuilder._SIGNS[tile](x, y) )
                
        return signs

    def _generateRandomObjects(map_size: Tuple[int, int]) -> Tuple[DuckieObject]:
        objects = ['tree', 'duckie']                  # add object
        hbounds = {'tree':   DuckieBHeight(0.3, 0.5), # add bounds
                'duckie': DuckieBHeight(0.08, 0.11)}
        
        round2f = lambda f: float(f'{f:.2f}')

        width, height = map_size
        positions = pds(width, height, r=0.75)

        res = [
            DuckieObject(obj:=random.choice(objects), 
                random.randint(0, 359), 
                round2f(y),                      # real x
                round2f(x - width + height - 1), # real y
                round2f(hbounds[obj].min + random.random() * hbounds[obj].dh)) for x, y in positions
        ]

        return res

    def _getMapOfVisibleObjects(bitmap: np.ndarray, objects: Tuple[DuckieObject]) -> list[list[list[DuckieObject]]]:
        w, h = bitmap.shape[:2]
        moves = ((0, 1), (1, 0), (0, -1), (-1, 0))
        
        coords_obj2map = lambda x, y: (y + w - h + 1, x)

        result = [[[] for i in range(h)] for j in range(w)]
        
        for x in range(w):
            for y in range(h):
                if bitmap[x][y] == 0: 
                    continue
                
                cx, cy = x + 0.5, y + 0.5
                w_rect = RectArea(cx - 0.5, cx + 0.5, cy - 0.5, cy + 0.5)
                h_rect = RectArea(cx - 0.5, cx + 0.5, cy - 0.5, cy + 0.5)
                
                for dx, dy in moves:
                    if not (0 <= x + dx < w and 0 <= y + dy < h):
                        continue
                    if bitmap[x+dx, y+dy] == 0:
                        continue

                    if dx < 0:
                        w_rect.x_min += dx
                    else:
                        w_rect.x_max += dx
                    if dy < 0:
                        h_rect.y_min += dy
                    else:
                        h_rect.y_max += dy

                for obj in objects:
                    ox, oy = coords_obj2map(obj.x, obj.y)
                    if  (ox, oy) in w_rect or (ox, oy) in h_rect:
                        result[x][y].append(obj)

        return result

    def _saveMap(file_name: str, 
                duckie: DuckieMap, 
                signs: Tuple[DuckieObject], 
                randomness: Tuple[DuckieObject]):
        """Saves Duckietown map with valid format"""

        tiles = duckie.tiles

        with open(file_name, 'w') as file_map:
            file_map.write('tiles:\n')

            for tile_line in tiles:
                line = ', '.join(tile_line)
                file_map.write(f'  - [{line}]\n')
            
            file_map.write('objects:' + '\n')
            
            for i, sign in enumerate(signs, 1):
                file_map.write(
                    sign.toGym(f'sign{i}')
                )

            for i, obj in enumerate(randomness, 1):
                file_map.write(
                    obj.toGym(f'{obj.type}{i}')
                )

            file_map.write('tile_size: 0.585')
    
    def load(name: str) -> np.ndarray:
        """TODO: load bitmap from file"""
        print(f'[MapBuilder] Load \'{name}\'')

        bitmap = np.full((10, 10), 255, dtype=np.uint8)

        return bitmap

    def parse(name: str, bitmap: np.ndarray, *, inject=False, random=False, getvisible=False):
        """Parses bitmap and writes it file"""
        print(f'[MapBuilder] Parse \'{name}\'')

        duckie = MapBuilder._bitmap2duckie(bitmap)
        signs  = MapBuilder._duckie2signs(duckie)
        randomness = MapBuilder._generateRandomObjects((duckie.width, duckie.height)) if random else tuple()

        if inject:
            name = expanduser(f'{MapBuilder._MAPS_PATH}/{name}.yaml')
        else:
            name = f'{name}.txt'

        MapBuilder._saveMap(name, duckie, signs, randomness)

        return MapBuilder._getMapOfVisibleObjects(bitmap, signs + randomness) if getvisible else None

if __name__ == '__main__':
    generated = MapGenerator.generate((5, 8), show_generation=True)

    visible = MapBuilder.parse('generated', generated, inject=True, random=True, getvisible=True)

    window_size = (480, 480)

    view = np.array(generated)
    width, height = view.shape[:2]
    scale = min(window_size[0]//width, window_size[1]//height)

    # mouse callback function
    def get_objects(event,x,y,flags,param):
        if event == cv2.EVENT_LBUTTONDBLCLK:
            print(visible[y//scale][x//scale], x//scale, y//scale)
    
    cv2.namedWindow('visible')
    cv2.setMouseCallback('visible', get_objects)

    while True:
        view = cv2.resize(view, (height*scale, width*scale), interpolation=cv2.INTER_AREA)
        cv2.imshow("visible", view)
        if cv2.waitKey(25) & 0xFF == 27:
            break

    cv2.destroyAllWindows()