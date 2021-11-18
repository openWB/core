from ..helpermodules import log
from ..helpermodules import pub


def pub_configurable():
    """ published eine Liste mit allen konfigurierbaren SoC-Modulen sowie allen Devices mit den möglichen Komponenten.
    """
    _pub_configurable_soc_modules()
    _pub_configurable_devices_components()
    _pub_configurable_chargepoints()


def _pub_configurable_soc_modules() -> None:
    try:
        soc_modules = [
            {
                "value": "tesla",
                "text": "Tesla"
            }
        ]
        pub.pub("openWB/set/system/configurable/soc_modules", soc_modules)
    except Exception:
        log.MainLogger().exception("Fehler im configuration-Modul")


def _pub_configurable_devices_components() -> None:
    try:
        devices_components = [
            {
                "value": "alpha_ess",
                "text": "Alpha ESS",
                "component": [
                    {
                        "value": "bat",
                        "text": "Alpha Ess-Speicher"
                    },
                    {
                        "value": "cointer",
                        "text": "Alpha Ess-Zähler"
                    },
                    {
                        "value": "inverter",
                        "text": "Alpha Ess-Wechselrichter"
                    }
                ]
            },
            {
                "value": "openwb",
                "text": "openWB Kit",
                "component": [
                    {
                        "value": "bat",
                        "text": "Speicher-Kit"
                    },
                    {
                        "value": "counter",
                        "text": "EVU-Kit"
                    },
                    {
                        "value": "inverter",
                        "text": "PV-Kit"
                    }
                ]
            },
            {
                "value": "openwb_flex",
                "text": "openWB Kit flex",
                "component": [
                    {
                        "value": "bat",
                        "text": "Speicher-Kit flex"
                    },
                    {
                        "value": "counter",
                        "text": "EVU-Kit flex"
                    },
                    {
                        "value": "inverter",
                        "text": "PV-Kit flex"
                    }
                ]
            },
            {
                "value": "mqtt",
                "text": "MQTT-Device",
                "component": [
                    {
                        "value": "bat",
                        "text": "MQTT-Speicher"
                    },
                    {
                        "value": "counter",
                        "text": "MQTT-Zähler"
                    },
                    {
                        "value": "inverter",
                        "text": "MQTT-Wechselrichter"
                    }
                ]
            }
        ]
        pub.pub("openWB/set/system/configurable/devices_components", devices_components)
    except Exception:
        log.MainLogger().exception("Fehler im configuration-Modul")


def _pub_configurable_chargepoints() -> None:
    try:
        chargepoints = [
            {
                "value": "openwb_daemon",
                "text": "openWB Daemon"
            },
            {
                "value": "openwb_ip_evse",
                "text": "openWB IP-EVSE"
            }
        ]
        pub.pub("openWB/set/system/configurable/chargepoints", chargepoints)
    except Exception:
        log.MainLogger().exception("Fehler im configuration-Modul")
