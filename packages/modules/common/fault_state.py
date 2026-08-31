import logging
import traceback
from types import TracebackType
from typing import Optional, Callable, Type, TypeVar

from helpermodules import exceptions
from helpermodules.pub import Pub
from helpermodules.constants import NO_ERROR
from modules.common import component_type
from modules.common.component_setup import ComponentSetup
from modules.common.fault_state_level import FaultStateLevel

log = logging.getLogger(__name__)


class ComponentInfo:
    def __init__(self,
                 id: Optional[int],
                 name: str,
                 type: str,
                 hostname: str = "localhost",
                 hierarchy_id: Optional[int] = None) -> None:
        self.id = id
        self.name = name
        self.type = type
        self.hostname = hostname
        self.hierarchy_id = hierarchy_id

    @staticmethod
    def from_component_config(component_config: ComponentSetup,
                              hostname: str = "localhost"):
        return ComponentInfo(component_config.id,
                             component_config.name,
                             component_config.type,
                             hostname)


class FaultState(Exception):
    def __init__(self, component_info: ComponentInfo) -> None:
        self.component_info = component_info
        self.fault_str = NO_ERROR
        self.fault_state = FaultStateLevel.NO_ERROR

    def store_error(self) -> None:
        try:
            if self.fault_state != FaultStateLevel.NO_ERROR:
                log.error(self.component_info.name + ": FaultState " +
                          str(self.fault_state) + ", FaultStr " +
                          self.fault_str + ", Traceback: \n" +
                          traceback.format_exc())
            topic = component_type.type_to_topic_mapping(self.component_info.type)
            if (self.component_info.type == component_type.ComponentType.FLEXIBLE_TARIFF.value or
                    self.component_info.type == component_type.ComponentType.GRID_FEE.value):
                topic_prefix = f"openWB/set/{topic}"
            else:
                topic_prefix = f"openWB/set/{topic}/{self.component_info.id}"
            Pub().pub(f"{topic_prefix}/get/fault_str", self.fault_str)
            Pub().pub(f"{topic_prefix}/get/fault_state", self.fault_state.value)
            if self.component_info.type == "internal_chargepoint":
                Pub().pub(f"openWB/set/chargepoint/{self.component_info.hierarchy_id}/get/fault_str",
                          self.fault_str)
                Pub().pub(f"openWB/set/chargepoint/{self.component_info.hierarchy_id}/get/fault_state",
                          self.fault_state.value)
        except Exception:
            log.exception("Fehler im Modul fault_state")

    def error(self, message: str) -> None:
        self.fault_str = message
        self.fault_state = FaultStateLevel.ERROR

    def warning(self, message: str) -> None:
        self.fault_str = message
        self.fault_state = FaultStateLevel.WARNING

    def no_error(self, message: Optional[str] = None) -> None:
        if message:
            self.fault_str = message
        else:
            self.fault_str = NO_ERROR
        self.fault_state = FaultStateLevel.NO_ERROR

    def from_exception(self, exception: Optional[Exception] = None) -> None:
        if isinstance(exception, FaultState):
            self.fault_str = exception.fault_str
            self.fault_state = exception.fault_state
        else:
            self.fault_str, self.fault_state = exceptions.get_default_exception_registry().translate_exception(
                exception)


class FaultStateContext:
    def __init__(self, fault_state: FaultState, update_always: bool = True, reraise: bool = False) -> None:
        self.__fault_state = fault_state
        self.update_always = update_always
        self.reraise = reraise

    def __enter__(self) -> None:
        if self.update_always:
            self.__fault_state.no_error()
        return None

    def __exit__(self,
                 exc_type: Optional[Type[BaseException]],
                 exc_value: Optional[BaseException],
                 traceback: Optional[TracebackType]) -> bool:
        if isinstance(exc_value, Exception):
            self.__fault_state.from_exception(exc_value)
        elif self.update_always is False and self.__fault_state.fault_state == 0:
            # Fehlerstatus nicht überschreiben
            return True
        self.__fault_state.store_error()
        if self.reraise is False or exc_value is None:
            return True
        else:
            return False


T_C = TypeVar("T_C", bound=Callable)
