import pygame

from PIL import Image
import numpy as np
import OpenGL.GL as gl
import OpenGL.GLU as glu
import cv2

def drawData(data):
    shape = data.shape[:2]
    scale = min(100//shape[0], 100//shape[1])
    shape = shape[0] * scale, shape[1] * scale
    image_tmp = cv2.resize(data, dsize=shape, interpolation=cv2.INTER_AREA)

    Image.fromarray(image_tmp).save('data.bmp')
    im = Image.open('data.bmp')
    
    w, h, image = im.size[0], im.size[1], im.tobytes("raw", "RGB", 0, -1)

    texture_id = gl.glGenTextures(1)
    gl.glBindTexture(gl.GL_TEXTURE_2D, texture_id)
    gl.glPixelStorei(gl.GL_UNPACK_ALIGNMENT, 1)
    gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGB, 
        w, h, 0, gl.GL_RGB, gl.GL_UNSIGNED_BYTE, image)


def main():
    pygame.init()
    size = 500, 500

    pygame.display.set_mode(size, pygame.DOUBLEBUF | pygame.OPENGL)

    glu.gluPerspective(0, size[0]/size[1], 1, 10)
    gl.glTranslatef(0.0, 0.0, -5)
    gl.glClearColor(0, 1, 0, 0.1)

    data = np.zeros((10, 10, 3), dtype=np.uint8)
    data[4, :, :] = 255

    while True:
        # event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.display.quit()
                pygame.quit()
                quit()

        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

        gl.glEnable(gl.GL_TEXTURE_2D)
        drawData(data)
        gl.glDisable(gl.GL_TEXTURE_2D)

        pygame.display.flip()
        
if __name__ == '__main__':
    main()

