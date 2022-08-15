#Map generation using WFC

import random
from collections import namedtuple
import numpy as np
from PIL import Image
from tileproc.tile_processing import Tile, get_tiles, state2image
from utills import Direction
import cv2

class MapGenerator:
    def _show_view(state: np.ndarray, window_size: tuple[int, int] = (480, 480)) -> None:
        view = np.array(state)
        height, width = view.shape[:2]
        scale = min(window_size[0]//width, window_size[1]//height)

        view = cv2.resize(view, (width*scale, height*scale), interpolation=cv2.INTER_AREA)
        cv2.imshow("state", view)
        cv2.waitKey(1)
    def _nonzero(array: np.ndarray):
        """Like np.nonzero, except it makes sense."""
        transform = int if len(np.asarray(array).shape) == 1 else tuple
        
        return list(map(transform, np.transpose(np.nonzero(array))))
    def _minEntropyLocation(potential: np.ndarray) -> tuple[int, int] | None:
        num_choices = np.sum(potential, axis=2, dtype='float32')
        num_choices[num_choices == 1] = np.inf
        candidate_locations = MapGenerator._nonzero(num_choices == num_choices.min())
        
        location = random.choice(candidate_locations)
        
        if num_choices[location] == np.inf:
            return None
        
        return location
    def _addConstraint(tiles: list[Tile],
                    state:              np.ndarray, 
                    location:           tuple[int, int], 
                    incoming_direction: Direction, 
                    possible_tiles:     list[Tile]) -> bool:
        neighbor_constraint = {t.sides[incoming_direction.value] for t in possible_tiles}
        outgoing_direction = incoming_direction.reverse()
        changed = False

        for i, not_used in enumerate(state[location]):
            if not not_used:
                continue
            if tiles[i].sides[outgoing_direction.value] not in neighbor_constraint:
                state[location][i] = False
                changed = True
        
        if not np.any(state[location]):
            raise Exception(f"No patterns left at {location}")
        
        return changed
    def _propagate(tiles: list[Tile], state: np.ndarray, start_location: tuple[int, int]):
        height, width = state.shape[:2]
        needs_update = np.full((height, width), False)
        needs_update[start_location] = True

        while np.any(needs_update):
            needs_update_next = np.full((height, width), False)
            locations = MapGenerator._nonzero(needs_update)
            
            for location in locations:
                possible_tiles = [tiles[n] for n in MapGenerator._nonzero(state[location])]
            
                for direction, x, y in Direction.neighbors(location, height, width):
                    location = (x, y)
                    was_updated = MapGenerator._addConstraint(tiles, state, location,
                                                direction, possible_tiles)
                    needs_update_next[location] |= was_updated
            
            needs_update = needs_update_next
    def _nextIteration(tiles: list[Tile], weights: list[float], old_state: np.ndarray) -> np.ndarray:
        state = old_state.copy()
        to_collapse = MapGenerator._minEntropyLocation(state)
        
        if to_collapse is None:
            raise StopIteration()
        elif not np.any(state[to_collapse]):
            raise Exception(f"No choices left at {to_collapse}")
        else:
            nonzero = MapGenerator._nonzero(state[to_collapse])
            tile_probs = weights[nonzero]/sum(weights[nonzero])
            
            selected_tile = np.random.choice(nonzero, p=tile_probs)

            state[to_collapse] = False
            state[to_collapse][selected_tile] = True

            MapGenerator._propagate(tiles, state, to_collapse)
        
        return state
    def _tilemap2bitmap(last_state: np.ndarray) -> np.ndarray:
        end_state = last_state
        end_state = np.concatenate((
            [end_state[0,:]], 
            end_state, 
            [end_state[-1,:]]))
        end_state = np.concatenate((
            np.array([end_state[:,0]]).T, 
            end_state, 
            np.array([end_state[:,-1]]).T), axis=1)

        h, w = end_state.shape[:2]

        return cv2.resize(end_state, (w//2, h//2))

    def generate(size: tuple[int, int] = (10, 10), show_generation: bool = False):
        width, height = size
        width_pad  = width  % 2
        height_pad = height % 2
        width  //= 2
        height //= 2

        tiles = get_tiles()

        weights = np.asarray([tile.weight for tile in tiles])

        state = np.full((width, height, len(tiles)), True)

        cur_state = state
        while True:
            if show_generation:
                MapGenerator._show_view(state2image(cur_state, tiles))
            
            try:
                cur_state = MapGenerator._nextIteration(tiles, weights, cur_state)
            except StopIteration as e:
                break
            except Exception as e:
                print(e)
                break

        if show_generation:
            MapGenerator._show_view(state2image(cur_state, tiles))
            cv2.waitKey(0)


        final_map = MapGenerator._tilemap2bitmap(np.array(state2image(cur_state, tiles)))

        final_map = final_map[:width*2+width_pad,:height*2+height_pad]

        Image.fromarray(final_map).save("resources/map.png")

        cv2.destroyAllWindows()

        return final_map

if __name__ == '__main__':
    generated = MapGenerator.generate((7, 2), show_generation=True)