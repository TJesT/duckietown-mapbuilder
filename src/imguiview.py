from .model import DataStock, MapData
from .mapbuilder import MapBuilder

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Tuple

import numpy as np
import pygame
import OpenGL.GL as gl

from imgui.integrations.pygame import PygameRenderer
import imgui

@dataclass(init=True, repr=True, eq=True)
class _Item:
    label: str
    shortcut: str
    onClick: Callable[..., None]

@dataclass(init=True, repr=True, eq=True)
class _Window:
    label: str
    settings: Dict[str, Any]
    onSuccess: Callable[..., None]
    opened: bool = False

    def setOpened(self):
        self.opened = True


class View(ABC):
    @abstractmethod
    def setup(self, stock: Optional[DataStock], *, size: Tuple):
        pass

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def stop(self):
        pass


class PygameImguiView(View):
    def __init__(self):
        super().__init__()
        self.main_menu = dict()
        self.map_menu  = dict()
        self._delete_list = list()

    def setup(self, stock: Optional[DataStock] = DataStock(), *, size: tuple) -> None:
        '''View setup. Call after init.'''

        MAP_NEW_WINDOW = _Window("New", 
            dict(name="new_map", width=10, height=10, inject=False), 
            self._newMapOnClick)
        MAP_LOAD_WINDOW = _Window("Load", 
            dict(name="new_map"), 
            self._loadMapOnClick)

        QUIT_ITEM = tuple([_Item("Quit", "Cmd+Q", self.stop)])
        SAVE_MAP_ITEM = tuple([_Item("Save", None, MapBuilder.parse)])

        self._main_bar_windows = [
            MAP_NEW_WINDOW, MAP_LOAD_WINDOW
        ]

        if 'File' not in self.main_menu:
            self.main_menu['File'] = tuple()
        for window in self._main_bar_windows:
            self.main_menu['File'] += tuple([_Item(window.label, None, window.setOpened)])
        self.main_menu['File'] += QUIT_ITEM

        if 'File' not in self.map_menu:
            self.map_menu['File'] = tuple()
        self.map_menu['File'] += SAVE_MAP_ITEM

        self._size = size[:2]
        self._stock = stock

        pygame.init()
        pygame.display.set_mode(self._size, pygame.DOUBLEBUF | pygame.OPENGL | pygame.RESIZABLE)
        
        imgui.create_context()

        self._impl = PygameRenderer()

        self._io = imgui.get_io()
        self._io.display_size = self._size

        self._running = True
    
    def run(self):
        """Runs gui main cycle"""
        print('[View] Run')
        while self._running:
            self._render()
        
        self._closeWindow()

    def stop(self):
        print('[View] Stop')
        self._running = False

    def _closeWindow(self):
        pygame.display.quit()
        pygame.quit()

    def _render(self):
        # proccess events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.stop()
                return
            self._impl.process_event(event)
            
        self._impl.process_inputs()

        # prepare frame
        imgui.new_frame()
        self._clearScreen()
        self._drawFrame()

        # show frame
        imgui.render()
        self._impl.render(imgui.get_draw_data())
        pygame.display.flip()

    def _newMapOnClick(self, *, name, width, height, inject):
        print(f'[View][MainMenu][onClick] New')
        self._stock.addData(name, MapData(name, (width, height), inject=inject))

    def _loadMapOnClick(self, *, name):
        print(f'[View][MainMenu][onClick] Load')
        data = MapBuilder.load(name)
        self._stock.addData(name, MapData(name, data.shape[:2], data))

    def _Window_updateSettings(self, imw: _Window):
        for setting in imw.settings:
            match imw.settings[setting]:
                case bool():
                    _, imw.settings[setting] = imgui.checkbox(setting, imw.settings[setting])
                case int():
                    _, imw.settings[setting] = imgui.input_int(setting, imw.settings[setting])
                case str():
                    _, imw.settings[setting] = imgui.input_text(setting, imw.settings[setting], 20)

    def _Window_draw(self, imw: _Window):
        with imgui.begin(imw.label,
                        flags=imgui.WINDOW_NO_COLLAPSE 
                        | imgui.WINDOW_NO_RESIZE 
                        | imgui.WINDOW_ALWAYS_AUTO_RESIZE) as window:
            if window.opened:
                self._Window_updateSettings(imw)

                if imgui.button('OK'):
                    imw.onSuccess(**imw.settings)
                    imw.opened = False
            else:
                imw.opened = False
        
    def _Data_draw(self, model_name):
        model = self._stock.getData(model_name)
        w, h = model.getSize()
        butt_size = 20, 20
        
        with imgui.begin(model_name, closable=True, 
                        flags=imgui.WINDOW_NO_RESIZE
                        | imgui.WINDOW_ALWAYS_AUTO_RESIZE) as window:
            if window.opened:
                for menu_name in self.map_menu:
                    self._Menu_add(menu_name, self.map_menu[menu_name], model.__dict__)
                imgui.push_style_var(imgui.STYLE_ITEM_SPACING, (0.0, 0.0))
                for y in range(h):
                    for x in range(w):
                        if x > 0:
                            imgui.same_line()
                        imgui.push_id(f'{y*w + x}')
                        color = model.value2color(model.getValue(x, y))
                        if imgui.color_button('', *color, *butt_size):
                            model.buttonOnClick(x, y)
                        imgui.pop_id()
                imgui.pop_style_var()
            else:
                self._delete_list.append(model_name)
                    
    def _Menu_add(self, menu_name: str, items: Tuple[_Item], item_args: dict = dict()):
        for item in items:
            if imgui.begin_menu(menu_name, True):
                clicked, selected = imgui.menu_item(
                    item.label, item.shortcut, False, True
                )
                if clicked:
                    item.onClick(**item_args)
                imgui.end_menu()

    def _MainMenu_draw(self):
        with imgui.begin_main_menu_bar() as menu:
            if menu.opened:
                for menu_name in self.main_menu:
                    self._Menu_add(menu_name, self.main_menu[menu_name])

    def _drawAdditionalWindows(self):
        for window in self._main_bar_windows:
            if window.opened:
                self._Window_draw(window)

    def _Data_clear(self):
        while len(self._delete_list) > 0:
            self._stock.delData(self._delete_list.pop())

    def _drawFrame(self):
        self._MainMenu_draw()

        self._drawAdditionalWindows()

        for model_name in self._stock.getNames():
            self._Data_draw(model_name)

        self._Data_clear()

        # imgui.show_test_window()

    def _clearScreen(self):
        gl.glClearColor(0, 0, 0, 1)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)

