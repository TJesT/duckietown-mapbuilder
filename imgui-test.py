from dataclasses import dataclass
from typing import Callable, Dict, Tuple

import pygame
import OpenGL.GL as gl

from imgui.integrations.pygame import PygameRenderer
import imgui

@dataclass(init=True, repr=True, eq=True)
class _Item:
    label: str
    shortcut: str
    onClick: Callable[[], None]

class PygameView:
    _BACKGROUND_COLOR_RGBA = (0, 0, 0, 1)

    def __init__(self, main_menu: Dict[str, Tuple[_Item]]=dict(), *, size: tuple) -> None:
        self._main_menu = main_menu
        self._main_menu['File'] += tuple([_Item("Quit", "Cmd+Q", self.stop)])

        self._size = size[:2]

        pygame.init()
        pygame.display.set_mode(self._size, pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE)
        
        imgui.create_context()

        self._impl = PygameRenderer()

        self._io = imgui.get_io()
        self._io.display_size = self._size

        self._running = True
    
    def run(self):
        """Runs gui main cycle"""
        while self._running:
            self._render()
        
        self._closeWindow()

    def stop(self):
        self._running = False

    def _closeWindow(self):
        pygame.display.quit()
        pygame.quit()

    def _mainMenu_addMenu(self, menu_name: str, items: Tuple[_Item]):
        for item in items:
            if imgui.begin_menu(menu_name, True):
                clicked, selected = imgui.menu_item(
                    item.label, item.shortcut, False, True
                )
                if clicked:
                    item.onClick()
                imgui.end_menu()

    def _drawFrame(self):
        with imgui.begin_main_menu_bar():
            for menu_name in self._main_menu:
                self._mainMenu_addMenu(menu_name, self._main_menu[menu_name])

        with imgui.begin("New window !!!") as window:
            if window.opened:
                imgui.text_ansi_colored("Hellow world!", 1, 0, 0)
        
        imgui.show_test_window()
    
    def _clearScreen(self):
        gl.glClearColor(*self._BACKGROUND_COLOR_RGBA)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

    def _render(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.stop()
                return
            self._impl.process_event(event)
            
        self._impl.process_inputs()

        imgui.new_frame()

        self._clearScreen()

        self._drawFrame()

        imgui.render()
        self._impl.render(imgui.get_draw_data())
        pygame.display.flip()



if __name__ == '__main__':
    main_menu = dict(
        File=tuple(
            [_Item("Else!", "No bind", lambda: print("Hmmm.. Hi ?? ><"))]
        ),
        Else=tuple(
            [_Item("None", None, lambda: None),
             _Item("Greet", "No bind", lambda: print("Hi !! Nice 2 meet you ^^"))]
        ))
    
    view = PygameView(main_menu, size=(600,800))
    view.run()