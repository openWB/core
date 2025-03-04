import logging
import paho.mqtt.subscribe as subscribe


log = logging.getLogger(__name__)


def sub_single(topic, hostname="localhost", port=1883):
    """ subscribed ein einzelnes Topic eines Hosts, der nicht der localhost ist.

        Parameter
    ---------
    topic : str
        Topic, das subscribed werden soll
    hostname: str
        IP des Hosts
    """
    return subscribe.simple(topic, hostname=hostname, port=port)
