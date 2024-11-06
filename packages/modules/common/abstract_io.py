from abc import abstractmethod
from typing import Dict


class AbstractIoDevice:
    @abstractmethod
    def __init__(self, io_config: dict) -> None:
        pass

    @abstractmethod
    def read(self) -> None:
        pass

    @abstractmethod
    def write(self, digital_output: Dict[int, int]) -> None:
        pass


class AbstractIoAction:
    def __init__(self):
        self.timestamp = None

    @abstractmethod
    def setup(self) -> None:
        pass
