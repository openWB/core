import logging
import paho.mqtt.client as mqtt
import time

log = logging.getLogger(__name__)


class InternalBroker:
    def __init__(self, name, on_connect, on_message) -> None:
        try:
            client = mqtt.Client(f"openWB-{name}-{self._get_serial()}")
            client.on_connect = on_connect
            client.on_message = on_message
            client.connect("localhost", 1886)
            client.loop_start()
            time.sleep(1)
            client.loop_stop()
        except Exception:
            log.exception("Fehler beim Abonnieren des internen Brokers")

    def _get_serial(self):
        """ Extract serial from cpuinfo file
        """
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line[0:6] == 'Serial':
                    return line[10:26]
            return "0000000000000000"
