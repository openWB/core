from abc import abstractmethod


class AbstractChargepoint:
    @abstractmethod
    def __init__(self, config: dict) -> None:
        pass

    @abstractmethod
    def set_current(self, current: float) -> None:
        pass

    @abstractmethod
    def get_values(self) -> None:
        pass

    @abstractmethod
    def switch_phases(self, phases_to_use: int, duration: int) -> None:
        pass
