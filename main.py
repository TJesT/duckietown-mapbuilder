import numpy as np
import png
import cv2
from mapbuilder import MapBuilder

S = 600 #высота экрана

map_name = input('Имя файла (без расширения): ')
h        = int(input('Высота: '))
w        = int(input('Ширина: '))
inject   = input('Загружать в duckie-world: ').lower() == "да"

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

MapBuilder.parse(map_name, nul, inject=inject)
