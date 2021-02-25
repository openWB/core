"""Modul, das die publish-Verbindung zum Broker bereit stellt.
"""

import json
import os
import paho.mqtt.client as mqtt

client = None


def setup_connection():
    """ öffnet die Verbindugn zum Broker. Bei Verbindungsabbruch wird automatisch versucht, eine erneute Verbindung herzustellen.
    """
    global client
    client = mqtt.Client("openWB-python-bulkpublisher-" + str(os.getpid()))
    client.connect("localhost")
    client.loop_start()


def pub(topic, payload):
    """ published das übergebene Payload als json-Objekt an das übergebene Topic.

    Parameter
    ---------
    topic : str
        Topic, an das gepusht werden soll

    payload : int, str, list, float
        Payload, der gepusht werden soll
    """
    client.publish(topic, payload=json.dumps(payload), qos=0, retain=True)


def delete_connection():
    """ schließt die Verbindung zum Broker.
    """
    client.loop_stop()
    client.disconnect
