import logging
import threading
from typing import Callable, Optional, List, Union, Any, Dict
from helpermodules.constants import NO_ERROR

from modules.common.fault_state import ComponentInfo, FaultState, FaultStateLevel

log = logging.getLogger(__name__)


class SingleComponentUpdateContext:
    """ Wenn die Werte der Komponenten nicht miteinander verrechnet werden, sollen, auch wenn bei einer Komponente ein
    Fehler auftritt, alle anderen dennoch ausgelesen werden. WR-Werte dienen nur statistischen Zwecken, ohne
    EVU-Werte ist aber keine Regelung möglich. Ein nicht antwortender WR soll dann nicht die Regelung verhindern.
        for component in self.components:
            with SingleComponentUpdateContext(component):
                component.update()
    """

    def __init__(self,
                 fault_state: FaultState,
                 error_handler: Callable = None,
                 update_always: bool = True,
                 reraise: bool = False):
        self.__fault_state = fault_state
        self.update_always = update_always
        self.reraise = reraise
        self.error_handler = error_handler

    def __enter__(self):
        log.debug("Update Komponente ['"+self.__fault_state.component_info.name+"']")
        if self.update_always:
            self.__fault_state.no_error()
        return None

    def __exit__(self, exception_type, exception, exception_traceback) -> bool:
        MultiComponentUpdateContext.override_subcomponent_state(self.__fault_state, exception, self.update_always)
        if isinstance(exception, Exception) and self.error_handler is not None:
            self.error_handler()
        if self.reraise is False:
            return True
        else:
            return False


class MultiComponentUpdateContext:
    """ Wenn die Werte der Komponenten miteinander verrechnet werden, muss, wenn bei einer Komponente ein Fehler
    auftritt, für alle Komponenten der Fehlerzustand gesetzt werden, da aufgrund der Abhängigkeiten für alle Module
    keine Werte ermittelt werden können.
        with MultiComponentUpdateContext(self.components):
            for component in self.components:
                component.update()
    """
    __thread_local = threading.local()

    def __init__(self, device_components: Union[Dict[Any, Any], List[Any]], error_handler: Optional[callable] = None):
        self.__device_components = \
            device_components.values() if isinstance(device_components, dict) else device_components
        self.__ignored_components = []  # type: List[ComponentInfo]
        self.error_handler = error_handler

    def __enter__(self):
        if hasattr(self.__thread_local, "active_context"):
            raise Exception("Nesting MultiComponentUpdateContext is not supported")
        MultiComponentUpdateContext.__thread_local.active_context = self
        log.debug("Update Komponenten " +
                  str([component.fault_state.component_info.name for component in self.__device_components]))
        for component in self.__device_components:
            component.fault_state.fault_state = FaultStateLevel.NO_ERROR
            component.fault_state.fault_str = NO_ERROR
        return None

    def __exit__(self, exception_type, exception, exception_traceback) -> bool:
        for component in self.__device_components:
            fault_state = component.fault_state
            if fault_state not in self.__ignored_components:
                if exception:
                    fault_state.from_exception(exception)
                fault_state.store_error()
        delattr(MultiComponentUpdateContext.__thread_local, "active_context")
        if isinstance(exception, Exception) and self.error_handler is not None:
            self.error_handler()
        return True

    def ignore_subcomponent_state(self, component: ComponentInfo):
        self.__ignored_components.append(component)

    @staticmethod
    def override_subcomponent_state(fault_state: FaultState, exception, update_always: bool):
        active_context = getattr(
            MultiComponentUpdateContext.__thread_local, "active_context", None
        )  # type: Optional[MultiComponentUpdateContext]
        if active_context:
            # If a MultiComponentUpdateContext is active, we need make sure that it will not override
            # the value for the individual component
            active_context.ignore_subcomponent_state(fault_state)

        if exception:
            fault_state.from_exception(exception)
        elif update_always is False:
            # Fehlerstatus nicht überschreiben
            return
        fault_state.store_error()
