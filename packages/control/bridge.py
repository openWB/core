from typing import Dict


def get_default_config() -> Dict:
    return {
        "name": "NeueBruecke",
        "active": False,
        "remote": {
            "is_openwb_cloud": False,
            "username": "",
            "password": "",
            "client_id": "openWB",
            "host": "",
            "port": 1886,
            "prefix": "openWB/",
            "protocol": "mqttv311",
            "tls_version": "auto",
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
            "is_openwb_cloud": True,
            "username": "",
            "password": "",
            "client_id": "openWB",
            "host": "web.openwb.de",
            "port": 1883,
            "prefix": "",
            "protocol": "mqttv311",
            "tls_version": "auto",
            "try_private": True
        },
        "data_transfer": {
            "status": True,
            "graph": True,
            "configuration": True
        }
    }
