import json
import logging
import paho.mqtt.publish as publish

from helpermodules.broker import InternalBrokerPublisher


log = logging.getLogger(__name__)


class PubSingleton:
    def __init__(self) -> None:
        self.publisher = InternalBrokerPublisher()
        self.publisher.start_loop()

    def pub(self, topic: str, payload, qos: int = 0, retain: bool = True) -> None:
        if payload == "":
            self.publisher.client.publish(topic, payload, qos=qos, retain=retain)
        else:
            self.publisher.client.publish(topic, payload=json.dumps(payload), qos=qos, retain=retain)


class Pub:
    instance = None

    def __init__(self) -> None:
        if not Pub.instance:
            Pub.instance = PubSingleton()

    def __getattr__(self, name):
        return getattr(self.instance, name)


def pub_single(topic, payload, hostname="localhost", port=1883, no_json=False, retain=True):
    """ Sendet eine einzelne Nachricht an einen Host.

        Parameter
    ---------
    topic : str
        Topic, an das gesendet werden soll
    payload : int, str, list, float
        Payload, der gesendet werden soll. Nicht als json, da ISSS kein json-Payload verwendet.
    hostname: str
        IP des Hosts
    no_json: bool
        Kompatibilität mit ISSS, die ramdisk verwenden.
    """
    if hostname == "localhost":
        Pub().pub(topic, payload, qos=0, retain=retain)
        return

    if no_json:
        publish.single(topic, payload, hostname=hostname, port=port, retain=retain)
    else:
        publish.single(topic, json.dumps(payload), hostname=hostname, port=port, retain=retain)
