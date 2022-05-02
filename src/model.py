from dataclasses import dataclass, field
from typing import Any, Optional, Protocol
import numpy as np

class ButtonPad(Protocol):
    def buttonOnClick(self, x, y) -> None:
        ...
    
    def getValue(self, x, y) -> Any:
        ...

    def value2color(self, arg: Any) -> tuple[float, float, float]:
        ...

    def getSize(self) -> tuple[int, int]:
        ...

class MapData:
    def __init__(self, 
            name: str, 
            size: Optional[tuple[int, int]] = (10, 10),
            bitmap: Optional[np.ndarray] = None,
            inject: bool = False):
        self.name = name
        self.bitmap = np.zeros(size, dtype=np.uint8) if bitmap is None else bitmap
        self.inject = inject

    def buttonOnClick(self, x, y):
        print(f'[MapData][\'{self.name}\']({x=} {y=}) onClick')
        self.bitmap[x][y] ^= 255

    def getValue(self, x, y):
        return self.bitmap[x][y]

    def value2color(self, arg: int) -> tuple[float, float, float]:
        return (arg/255,) * 3

    def getSize(self):
        return self.bitmap.shape[:2]

@dataclass
class DataStock:
    models: dict[str, ButtonPad] = field(default_factory=dict)

    def addData(self, name: str, butt_pad: ButtonPad) -> None:
        print(f'[Stock][addData] {name=}')
        if name in self.models:
            raise KeyError(f"[Stock][addData] Data with name \'{name}\' already exists")
        
        self.models[name] = butt_pad

    def getData(self, name: str) -> ButtonPad:
        if name not in self.models:
            raise KeyError(f"[Stock][getData] Data with name \'{name}\' doesn't exists")
        
        return self.models[name]

    def delData(self, name: str) -> None:
        if name not in self.models:
            raise KeyError(f"[Stock][getData] Data with name \'{name}\' doesn't exists")
        
        del self.models[name]

    def getNames(self):
        return self.models.keys()


if __name__ == '__main__':
    stock = DataStock()
    data1 = MapData('data1', (4, 6))
    data2 = MapData('data2')
    stock.addData(data1.name, data1)
    stock.addData(data2.name, data2)

    print(stock.getData('data1').getSize(), stock.getData('data1').bitmap.shape)