import logging
from typing import Callable, Optional, TypeVar, Generic, Any

from helpermodules import timecheck
from helpermodules.pub import Pub
from modules.common.abstract_device import AbstractCounter
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_type import ComponentType
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.common.store._factory import get_component_value_store

T_CONSUMER = TypeVar("T_CONSUMER")


log = logging.getLogger(__name__)


class ConfigurableConsumer(Generic[T_CONSUMER]):
    def __init__(self,
                 consumer_config: T_CONSUMER,
                 initializer: Callable,
                 error_handler: Optional[Callable],
                 update: Optional[Callable],
                 set_power_limit: Optional[Callable],
                 switch_on: Optional[Callable],
                 switch_off: Optional[Callable],) -> None:
        self.consumer_config = consumer_config
        self.initializer = initializer
        self.error_handler = error_handler
        self.update = update
        self.set_power_limit = set_power_limit
        self.switch_on = switch_on
        self.switch_off = switch_off

        self.error_timestamp = None
        self.sim_counter = SimCounterConsumer(self.config.id, self.config.type)
        self.store = get_component_value_store(self.config.type, self.config.id)
        self.fault_state = FaultState(ComponentInfo(self.config.id, self.config.name, "consumer"))
        try:
            self.initializer()
        except Exception:
            log.exception(f"Initialisierung von Gerät {self.config.name} fehlgeschlagen")

    def error_handler(self) -> None:
        error_timestamp_topic = f"openWB/set/consumer/{self.config.id}/get/error_timestamp"
        if self.error_timestamp is None:
            self.error_timestamp = timecheck.create_timestamp()
            Pub().pub(error_timestamp_topic, self.error_timestamp)
            log.debug(f"Fehler bei Gerät {self.config.name} aufgetreten, "
                      f"Fehlerzeitstempel: {self.error_timestamp}")
        if timecheck.check_timestamp(self.error_timestamp, 60) is False:
            try:
                self.error_handler()
            except Exception:
                log.exception(f"Fehlerbehandlung für Gerät {self.config.name} fehlgeschlagen")
            else:
                log.debug(f"Fehlerbehandlung für Gerät {self.config.name} wurde durchgeführt.")

            self.error_timestamp = None
            Pub().pub(error_timestamp_topic, self.error_timestamp)

    def update(self):
        with SingleComponentUpdateContext(self.fault_state):
            if self.update is not None:
                self.store(self.update())

    def set_power_limit(self, power_limit: Any) -> None:
        with SingleComponentUpdateContext(self.fault_state):
            self.set_power_limit(power_limit)

    def switch_on(self) -> None:
        with SingleComponentUpdateContext(self.fault_state):
            self.switch_on()

    def switch_off(self) -> None:
        with SingleComponentUpdateContext(self.fault_state):
            self.switch_off()


def dependency_injection_devices_components(component: AbstractCounter):
    component.sim_counter.component_type = ComponentType.CONSUMER.value
    component.store = get_component_value_store(ComponentType.CONSUMER, component.component_config.id)
    component.fault_state.component_info.type = ComponentType.CONSUMER.value
