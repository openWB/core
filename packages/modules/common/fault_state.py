import logging
import traceback
from typing import Optional, Callable, TypeVar

from helpermodules import exceptions, pub
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
                 parent_id: Optional[int] = None,
                 parent_hostname: Optional[str] = None) -> None:
        self.id = id
        self.name = name
        self.type = type
        self.hostname = hostname
        self.parent_id = parent_id
        self.parent_hostname = parent_hostname

    @staticmethod
    def from_component_config(component_config: ComponentSetup,
                              hostname: str = "localhost",
                              parent_hostname: Optional[str] = None):
        return ComponentInfo(component_config.id,
                             component_config.name,
                             component_config.type,
                             hostname,
                             parent_hostname)


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
            if self.component_info.type == component_type.ComponentType.ELECTRICITY_TARIFF.value:
                topic_prefix = f"openWB/set/{topic}"
            else:
                topic_prefix = f"openWB/set/{topic}/{self.component_info.id}"
            pub.Pub().pub(f"{topic_prefix}/get/fault_str", self.fault_str)
            pub.Pub().pub(f"{topic_prefix}/get/fault_state", self.fault_state.value)
            if (self.component_info.parent_hostname and
                    self.component_info.parent_hostname != self.component_info.hostname):
                pub.pub_single(f"openWB/set/{topic}/{self.component_info.parent_id}/get/fault_str",
                               self.fault_str, hostname=self.component_info.parent_hostname)
                pub.pub_single(f"openWB/set/{topic}/{self.component_info.parent_id}/get/fault_state",
                               self.fault_state.value, hostname=self.component_info.parent_hostname)
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


T_C = TypeVar("T_C", bound=Callable)
