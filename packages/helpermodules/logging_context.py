from contextlib import contextmanager
from contextvars import ContextVar
import logging
from typing import Optional


# Alle Chargeboxen teilen sich einen Eventloop-Thread. ContextVar haelt die ID
# pro Task getrennt, auch ueber await hinweg; neue Kindtasks erben den Kontext.
# Der Contextmanager stellt beim Verlassen den vorherigen Kontext wieder her.
# Der Filter nutzt die ID auch fuer Bibliothekslogs, sonst den Threadnamen.
_ocpp_chargebox_id: ContextVar[Optional[str]] = ContextVar("ocpp_chargebox_id", default=None)


@contextmanager
def ocpp_logging_context(chargebox_id: Optional[str]):
    token = _ocpp_chargebox_id.set(chargebox_id)
    try:
        yield
    finally:
        _ocpp_chargebox_id.reset(token)


class OcppContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.ocpp_context = _ocpp_chargebox_id.get() or record.threadName
        return True
