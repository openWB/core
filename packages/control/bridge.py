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
