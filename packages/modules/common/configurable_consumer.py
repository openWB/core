import logging
from typing import TypeVar, Generic, Any

from helpermodules import timecheck
from helpermodules.pub import Pub
from modules.common.abstract_consumer import AbstractConsumer
from modules.common.abstract_device import AbstractCounter
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_type import ComponentType
from modules.common.store._factory import get_component_value_store

T_CONSUMER = TypeVar("T_CONSUMER")


log = logging.getLogger(__name__)


class ConfigurableConsumer(Generic[T_CONSUMER], AbstractConsumer):
    def __init__(self,
                 consumer: AbstractConsumer) -> None:
        self.__consumer = consumer
        self.error_timestamp = None
        try:
            self.__consumer.initializer()
        except Exception:
            log.exception(f"Initialisierung von Gerät {self.__consumer.config.name} fehlgeschlagen")

    def error_handler(self) -> None:
        error_timestamp_topic = f"openWB/set/system/device/{self.__consumer.config.id}/error_timestamp"
        if self.error_timestamp is None:
            self.error_timestamp = timecheck.create_timestamp()
            Pub().pub(error_timestamp_topic, self.error_timestamp)
            log.debug(f"Fehler bei Gerät {self.__consumer.config.name} aufgetreten, "
                      f"Fehlerzeitstempel: {self.error_timestamp}")
        if timecheck.check_timestamp(self.error_timestamp, 60) is False:
            try:
                self.__consumer.error_handler()
            except Exception:
                log.exception(f"Fehlerbehandlung für Gerät {self.__consumer.config.name} fehlgeschlagen")
            else:
                log.debug(f"Fehlerbehandlung für Gerät {self.__consumer.config.name} wurde durchgeführt.")

            self.error_timestamp = None
            Pub().pub(error_timestamp_topic, self.error_timestamp)

    def update(self):
        with SingleComponentUpdateContext(self.__consumer.fault_state):
            self.__consumer.update()

    def set_power_limit(self, power_limit: Any) -> None:
        with SingleComponentUpdateContext(self.__consumer.fault_state):
            self.__consumer.set_power_limit(power_limit)

    def switch_on(self) -> None:
        with SingleComponentUpdateContext(self.__consumer.fault_state):
            self.__consumer.switch_on()

    def switch_off(self) -> None:
        with SingleComponentUpdateContext(self.__consumer.fault_state):
            self.__consumer.switch_off()


def dependency_injection_devices_components(component: AbstractCounter):
    component.sim_counter.component_type = ComponentType.CONSUMER.value
    component.store = get_component_value_store(ComponentType.CONSUMER, component.component_config.id)
    component.fault_state.component_info.type = ComponentType.CONSUMER.value
