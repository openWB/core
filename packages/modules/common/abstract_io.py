from abc import abstractmethod
from typing import Dict


class AbstractIo:
    @abstractmethod
    def __init__(self, io_config: dict) -> None:
        pass

    @abstractmethod
    def read(self) -> None:
        pass

    @abstractmethod
    def write(self, digital_output: Dict[int, int]) -> None:
        pass
