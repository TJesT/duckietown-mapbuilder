from collections import namedtuple
import numpy as np
from PIL import Image

import cv2
Tile = namedtuple('Tile', ('name', 'bitmap', 'sides', 'weight'))

# TODO: replace hardcoded names with directory scanning
TILES_PATH = "resources/tiles"
TILE_NAMES = ['4way', '3way', 'bend', 'none', 'stgh']

def blend_many(images: list[Image.Image]) -> Image.Image:
    """Blends a sequence of images."""
    current, *images = images
    for i, image in enumerate(images):
        current = Image.blend(current, image, 1/(i+2))

    return current

def blend_tiles(selections: list[bool], tiles: list[Tile]) -> Image.Image:
    """
    Given a list of states (True if ruled out, False if not) for each tile,
    and a list of tiles, return a blend of all the tiles that haven't been
    ruled out.
    """
    to_blend = [tile.bitmap for tile, selected in zip(tiles, selections) if selected]

    return blend_many(to_blend)

def state2image(map_state: np.ndarray, tiles: list[Tile]) -> Image.Image:
    """
    Given a list of states for each tile for each position of the image, return
    an image representing the state of the map.
    """
    rows = []
    for row in map_state:
        rows.append([np.asarray(blend_tiles(selections, tiles)) for selections in row])

    rows = np.array(rows)
    n_rows, n_cols, tile_height, tile_width = rows.shape[:4]
    images = np.swapaxes(rows, 1, 2)

    return Image.fromarray(images.reshape(n_rows*tile_height, n_cols*tile_width))


def get_tile_names() -> list[str]:
    return TILE_NAMES.copy()

def _get_tile_sides(bitmap: np.ndarray) -> list[bool]:
    h, w = bitmap.shape[:2]
    side_centers = ((-1, h//2), (w//2, -1), (0, h//2), (w//2, 0))
    
    sides = [bitmap[center] == 255 for center in side_centers]

    return sides

def _get_tile_rotations(name: str, bitmap: Image.Image) -> list[Tile]:
    rotations = np.array([
        np.array(bitmap), 
        np.array(bitmap.transpose(Image.ROTATE_90)),
        np.array(bitmap.transpose(Image.ROTATE_180)),
        np.array(bitmap.transpose(Image.ROTATE_270))
        ])

    unique_states = np.unique(rotations, axis=0)
    unique_count  = len(unique_states)

    return [Tile(
                f'{name}_{i}', 
                Image.fromarray(map), 
                _get_tile_sides(map), 
                1/unique_count
            ) for i, map in enumerate(unique_states)]

def get_tiles() -> list[Tile]:
    tile_bitmaps = {name: Image.open(f'{TILES_PATH}/{name}.png') for name in TILE_NAMES}

    tiles = []
    for name in TILE_NAMES:
        tiles += _get_tile_rotations(name, tile_bitmaps[name])

    return tiles
