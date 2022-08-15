from logging import Logger
# import cv2
import numpy as np
from PIL import Image

print(f'[TileGenerator] Generating...')

corners = ((0,0,-1,-1), (0,-1,-1,0))

tile_none = np.zeros((4,4), dtype=np.uint8)
# cv2.imshow("4way", tile_none)

tile_4way = np.full((4,4), 255, dtype=np.uint8)
tile_4way[corners] = 0
# cv2.imshow("4way", tile_4way)

tile_3way = np.full((4,4), 255, dtype=np.uint8)
tile_3way[corners] = 0
tile_3way[0,:] = 0
# cv2.imshow("3way", tile_3way)

tile_stgh = np.full((4,4), 255, dtype=np.uint8)
tile_stgh[corners] = 0
tile_stgh[0,:] = 0
tile_stgh[-1,:] = 0
# cv2.imshow("stgh", tile_stgh)

tile_bend = np.full((4,4), 255, dtype=np.uint8)
tile_bend[corners] = 0
tile_bend[0,:] = 0
tile_bend[:,0] = 0
# cv2.imshow("bend", tile_bend)

# cv2.waitKey(0)

print(f'[TileGenerator] Saving...')

# TODO: make dir if doesn't exist

Image.fromarray(tile_none).save("resources/tiles/none.png")
Image.fromarray(tile_4way).save("resources/tiles/4way.png")
Image.fromarray(tile_3way).save("resources/tiles/3way.png")
Image.fromarray(tile_stgh).save("resources/tiles/stgh.png")
Image.fromarray(tile_bend).save("resources/tiles/bend.png")

# cv2.destroyAllWindows()

print(f'[TileGenerator] Done!')