from collections import namedtuple
from bridson import poisson_disc_samples as pds
from utills import *
from typing import Tuple
from os.path import expanduser
import numpy as np
import random

from map_generator import MapGenerator

class MapBuilder:
    _MAPS_PATH = '~/.local/lib/python3.8/site-packages/duckietown_world/data/gd1/maps'
    _MOVES = ((0, 1), (1, 0), (0, -1), (-1, 0))
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
        for dx, dy in MapBuilder._MOVES:
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
        
        neighbour = [False, ] * 4
        
        for i, (dx, dy) in enumerate(MapBuilder._MOVES):
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
        
        for i in range(0, w):
            for j in range (0, h):
                x = j
                y = i - w + h
                tile = tiles[i][j]

                if tile in MapBuilder._SIGNS.keys():
                    signs.extend( MapBuilder._SIGNS[tile](x, y) )
                
        return signs

    def _generateRandomObjects(map_size: Tuple[int, int]) -> Tuple[DuckieObject]:
        objects = ['tree', 'duckie']
        hbounds = {'tree':   DuckieBHeight(0.3, 0.5),
                'duckie': DuckieBHeight(0.08, 0.11)}
        
        width, height = map_size
        positions = pds(width, height, r=0.75)

        res = [
            DuckieObject(obj:=random.choice(objects), 
                random.randint(0, 359), 
                y, # real x
                x - width + height - 1, # real y
                hbounds[obj].min + random.random() * hbounds[obj].dh) for x, y in positions
        ]

        return res

    def _saveMap(file_name: str, duckie: DuckieMap, signs: Tuple[DuckieObject], randomness: Tuple[DuckieObject]):
        """Saves Duckietown map in valid format"""

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

            for i, tree in enumerate(randomness, 1):
                file_map.write(
                    tree.toGym(f'{tree.type}{i}')
                )

            file_map.write('tile_size: 0.585')
    
    def load(name: str) -> np.ndarray:
        """TODO: load bitmap from file"""
        print(f'[MapBuilder] Load \'{name}\'')

        bitmap = np.full((10, 10), 255, dtype=np.uint8)

        return bitmap

    def parse(name: str, bitmap: np.ndarray, *, inject=False, random=False):
        """Parses bitmap and writes it file"""
        print(f'[MapBuilder] Parse \'{name}\'')

        duckie = MapBuilder._bitmap2duckie(bitmap)
        signs  = MapBuilder._duckie2signs(duckie)
        randomness = tuple()
        if random:
            randomness = MapBuilder._generateRandomObjects((duckie.width, duckie.height))
        
        if inject:
            name = expanduser(f'{MapBuilder._MAPS_PATH}/{name}.yaml')
        else:
            name = f'{name}.txt'

        MapBuilder._saveMap(name, duckie, signs, randomness)

if __name__ == '__main__':
    generated = MapGenerator.generate((7, 4), show_generation=False)

    MapBuilder.parse('generated', generated, inject=True, random=True)