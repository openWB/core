from abc import abstractmethod
from typing import List, Optional

from control.consumer.consumer_data import ConsumerUsage


class AbstractConsumer:
    @abstractmethod
    def __init__(self, component_config, **kwargs) -> None:
        self.component_config = component_config
        self.kwargs = kwargs

    @abstractmethod
    def initializer(self):
        pass

    @abstractmethod
    def error_handler(self) -> None:
        pass

    @abstractmethod
    def update(self, *kwargs) -> None:
        pass

    @abstractmethod
    def set_power_limit(self, power_limit: Optional[int]) -> None:
        pass

    @abstractmethod
    def switch_on(self) -> None:
        pass

    @abstractmethod
    def switch_off(self) -> None:
        pass
