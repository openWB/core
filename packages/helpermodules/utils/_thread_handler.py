import logging
import threading
from typing import List

from control import data
log = logging.getLogger(__name__)


def thread_handler(threads: List[threading.Thread]) -> None:
    # Start them all
    for thread in threads:
        thread.start()

    # Wait for all to complete
    for thread in threads:
        thread.join(timeout=data.data.general_data.data.control_interval/3)

    for thread in threads:
        if thread.is_alive():
            log.error(f"{thread.name} konnte nicht innerhalb des Timeouts die Werte abfragen, die abgefragten "
                      "Werte werden nicht in der Regelung verwendet.")
