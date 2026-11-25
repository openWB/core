import logging
from abc import abstractmethod
from typing import Generic, TypeVar

from modules.common.component_context import SingleComponentUpdateContext

T = TypeVar("T")
log = logging.getLogger(__name__)


class ValueStore(Generic[T]):
    @abstractmethod
    def set(self, state: T) -> None:
        pass

    @abstractmethod
    def update(self) -> None:
        pass

    def zero_power_on_sustained_error(self) -> None:
        pass


class LoggingValueStore(Generic[T], ValueStore[T]):
    def __init__(self, delegate: ValueStore[T]):
        self.delegate = delegate

    def set(self, state: T) -> None:
        log.debug("Raw data %s", state)
        self.delegate.set(state)

    def update(self) -> None:
        try:
            log.info("Saving %s", self.delegate.state)
            self.delegate.update()
        except AttributeError:
            # Wenn keine Daten ausgelesen werden, fehlt das state-Attribut.
            pass
        except Exception:
            log.exception("Error while publishing module data")

    def zero_power_on_sustained_error(self) -> None:
        try:
            self.delegate.zero_power_on_sustained_error()
        except AttributeError:
            pass


def update_values(component):
    with SingleComponentUpdateContext(component.fault_state, update_always=False):
        if hasattr(component, "store"):
            if component.fault_state.error_duration_exceeded():
                try:
                    component.store.zero_power_on_sustained_error()
                except AttributeError:
                    # darf update() nicht blockieren
                    pass
            try:
                component.store.update()
            except AttributeError:
                # Wenn keine Daten ausgelesen werden, fehlt das state-Attribut. Die eigentliche Fehlermeldung würde
                # dann durch die Attribute-Error-Meldung überschrieben werden.
                pass
