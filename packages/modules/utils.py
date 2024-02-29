import logging
import threading

from control import data
from helpermodules import pub

log = logging.getLogger(__name__)


def wait_for_module_update_completed(event_module_update_completed: threading.Event, topic: str):
    timeout = data.data.general_data.data.control_interval/2
    event_module_update_completed.clear()
    pub.Pub().pub(topic, True)
    if event_module_update_completed.wait(timeout) is False:
        log.error("Daten wurden noch nicht vollständig empfangen. Timeout abgelaufen, fortsetzen der Regelung.")
