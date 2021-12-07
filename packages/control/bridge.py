from typing import Dict


def get_default_config() -> Dict:
    return {
        "name": "NeueBruecke",
        "active": False,
        "remote": {
            "user": "",
            "passwort": "",
            "client_id": "openWB",
            "host": "",
            "port": 1886,
            "prefix": "openWB/",
            "protocol": "mqttv311",
            "tls_version": "tlsv1.3",
            "try_private": False
        },
        "data_transfer": {
            "status": False,
            "graph": False,
            "configuration": False
        }
    }


def get_cloud_config() -> Dict:
    return {
        "name": "openWBCloud",
        "active": True,
        "remote": {
            "user": "",
            "passwort": "",
            "client_id": "openWB",
            "host": "web.openwb.de",
            "port": 1886,
            "prefix": "",
            "protocol": "mqttv311",
            "tls_version": "tlsv1.3",
            "try_private": True
        },
        "data_transfer": {
            "status": True,
            "graph": True,
            "configuration": True
        }
    }
