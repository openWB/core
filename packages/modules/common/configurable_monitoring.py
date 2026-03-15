import logging
from typing import Callable


log = logging.getLogger(__name__)


class ConfigurableMonitoring():
    def __init__(self,
                 start_initializer: Callable[[], None],
                 stop_initializer: Callable[[], None]) -> None:
        try:
            self._start_monitoring = start_initializer
            self._stop_monitoring = stop_initializer
        except Exception:
            log.exception("Fehler im Monitoring Modul")

    def start_monitoring(self):
        self._start_monitoring()

    def stop_monitoring(self):
        self._stop_monitoring()
