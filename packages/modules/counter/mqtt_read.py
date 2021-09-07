from. import set_values
from ...helpermodules import simcount
from ...helpermodules import log

class module(set_values.set_values):
    def __init__(self, index) -> None:
        super().__init__()
        self.data = {}

    def read(self):
        pass