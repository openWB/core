from abc import abstractmethod
from typing import Dict, Optional


class AbstractIoDevice:
    @abstractmethod
    def __init__(self, io_config: dict) -> None:
        pass

    @abstractmethod
    def read(self) -> None:
        pass

    @abstractmethod
    def write(self, analog_output: Optional[Dict[str, int]], digital_output: Optional[Dict[str, bool]]) -> None:
        pass


class AbstractIoAction:
    def __init__(self):
        self.timestamp = None

    @abstractmethod
    def setup(self) -> None:
        pass
