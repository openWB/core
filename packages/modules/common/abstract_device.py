from abc import abstractmethod
from typing import Optional, Type


class AbstractDevice:
    @abstractmethod
    def __init__(self, device_config: dict) -> None:
        pass

    @abstractmethod
    def add_component(self, component_config: dict) -> None:
        pass

    @abstractmethod
    def update(self) -> None:
        pass


class AbstractBat:
    @abstractmethod
    def __init__(self, component_config, **kwargs) -> None:
        self.component_config = component_config
        self.kwargs = kwargs

    @abstractmethod
    def initializer(self):
        pass

    @abstractmethod
    def update(self, *kwargs) -> None:
        pass

    @abstractmethod
    def set_power_limit(self, power_limit: Optional[int]) -> None:
        # power limit None heißt, auf maximale Speicherleistung setzen = Speicher-Begrenzung aufheben
        pass

    def power_limit_controllable(self) -> bool:
        return False


class AbstractCounter:
    @abstractmethod
    def __init__(self, component_config, **kwargs) -> None:
        self.component_config = component_config
        self.kwargs = kwargs

    @abstractmethod
    def initializer(self):
        pass

    @abstractmethod
    def update(self, *kwargs) -> None:
        pass


class AbstractInverter:
    @abstractmethod
    def __init__(self, component_config, **kwargs) -> None:
        self.component_config = component_config
        self.kwargs = kwargs

    @abstractmethod
    def initializer(self):
        pass

    @abstractmethod
    def update(self, *kwargs) -> None:
        pass

    @abstractmethod
    def set_power_limit(self, power_limit: float) -> None:
        # power_limit in Werten zwischen 0 und 1
        pass


class DeviceDescriptor:
    def __init__(self,
                 configuration_factory: Type,
                 compatibility_bat_active: bool = False,
                 compatibility_bat_note: Optional[str] = None,
                 compatibility_device_note: Optional[str] = None,
                 special_icon: Optional[str] = None):
        self.configuration_factory = configuration_factory
        self.compatibility_bat_active = compatibility_bat_active
        self.compatibility_bat_note = compatibility_bat_note
        self.compatibility_device_note = compatibility_device_note
        self.special_icon = special_icon
