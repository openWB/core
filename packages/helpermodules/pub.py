"""Modul, das die publish-Verbindung zum Broker bereit stellt.
"""

import json
import os
import paho.mqtt.client as mqtt

from . import log

client = None


def setup_connection():
    """ öffnet die Verbindugn zum Broker. Bei Verbindungsabbruch wird automatisch versucht, eine erneute Verbindung herzustellen.
    """
    try:
        global client
        client = mqtt.Client("openWB-python-bulkpublisher-" + str(os.getpid()))
        client.connect("localhost")
        client.loop_start()
    except Exception as e:
        log.exception_logging(e)

def pub(topic, payload):
    """ published das übergebene Payload als json-Objekt an das übergebene Topic.

    Parameter
    ---------
    topic : str
        Topic, an das gepusht werden soll

    payload : int, str, list, float
        Payload, der gepusht werden soll
    """
    try:
        if payload == "":
            client.publish(topic, payload, qos=0, retain=True)
        else:
            client.publish(topic, payload=json.dumps(payload), qos=0, retain=True)
    except Exception as e:
        log.exception_logging(e)

def pub_float(var, topic):
    """konvertiert die Daten der Ramdisk-Datei in Float und published diese als json-Objekt.

        Parameters
    ----------
    var : str
        Pfad zur Ramdisk-Datei
    topic : str
        Topic, in das gepublished wird
    """
    try:
        f = open( "/var/www/html/openWB/ramdisk/"+var , 'r')
        value =f.read()
        f.close()
        if value == '\n':
            value=float(0)
        else:
            value=float(value)
        pub(topic, value)
    except Exception as e:
        log.exception_logging(e)

def pub_dict(var, topic):
    """konvertiert die Daten der übergebenen Ramdisk-Datei in ein Dictionary und published dieses als json-Objekt.

        Parameters
    ----------
    var : str
        Pfad zu Ramdisk-Datei
    topic : str
        Topic, in das gepublished wird
    """
    try:
        payload = {}
        f = open( "/var/www/html/openWB/ramdisk/"+var , 'r')
        for line in f:
            if "," in line:
                value = line.rstrip('\n').split(",")
                payload[value[0]] = value[1]
        f.close()
        pub(topic, payload)
    except Exception as e:
        log.exception_logging(e)

def delete_connection():
    """ schließt die Verbindung zum Broker.
    """
    try:
        client.loop_stop()
        client.disconnect
    except Exception as e:
        log.exception_logging(e)
