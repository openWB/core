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


class LoggingValueStore(Generic[T], ValueStore[T]):
    def __init__(self, delegate: ValueStore[T]):
        self.delegate = delegate

    def set(self, state: T) -> None:
        log.debug("Raw data %s", state)
        self.delegate.set(state)

    def update(self) -> None:
        log.info("Saving %s", self.delegate.state)
        self.delegate.update()


def update_values(component):
    with SingleComponentUpdateContext(component.component_info, update_always=False):
        if hasattr(component, "store"):
            try:
                component.store.update()
            except AttributeError:
                # Wenn keine Daten ausgelesen werden, fehlt das state-Attribut. Die eigentliche Fehlermeldung würde
                # dann durch die Attribute-Error-Meldung überschrieben werden.
                pass
