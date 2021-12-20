from helpermodules.log import MainLogger
from helpermodules.pub import Pub


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
                "value": "evnotify",
                "text": "EVNotify"
            },
            {
                "value": "tesla",
                "text": "Tesla"
            }
        ]
        Pub().pub("openWB/set/system/configurable/soc_modules", soc_modules)
    except Exception:
        MainLogger().exception("Fehler im configuration-Modul")


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
                        "value": "counter",
                        "text": "Alpha Ess-Zähler"
                    },
                    {
                        "value": "inverter",
                        "text": "Alpha Ess-Wechselrichter"
                    }
                ]
            },
            {
                "value": "carlo_gavazzi",
                "text": "Carlo Gavazzi",
                "component": [
                    {
                        "value": "counter",
                        "text": "Carlo Gavazzi-Zähler"
                    }
                ]
            },
            {
                "value": "fronius",
                "text": "Fronius",
                "component": [
                    {
                        "value": "bat",
                        "text": " Fronius Speicher"
                    },
                    {
                        "value": "counter_s0",
                        "text": "Fronius S0 Zähler"
                    },
                    {
                        "value": "counter_sm",
                        "text": "Fronius Smart Meter"
                    },
                    {
                        "value": "inverter",
                        "text": "Fronius Wechselrichter"
                    }
                ]
            },
            {
                "value": "http",
                "text": "HTTP",
                "component": [
                    {
                        "value": "bat",
                        "text": "HTTP-Speicher"
                    },
                    {
                        "value": "counter",
                        "text": "HTTP-Zähler"
                    },
                    {
                        "value": "inverter",
                        "text": "HTTP-Wechselrichter"
                    }
                ]
            },
            {
                "value": "huawei",
                "text": "Huawei",
                "component": [
                    {
                        "value": "bat",
                        "text": "Huawei-Speicher"
                    },
                    {
                        "value": "counter",
                        "text": "Huawei-Zähler"
                    },
                    {
                        "value": "inverter",
                        "text": "Huawei-Wechselrichter"
                    }
                ]
            },
            {
                "value": "janitza",
                "text": "Janitza",
                "component": [
                    {
                        "value": "counter",
                        "text": "Janitza-Zähler"
                    }
                ]
            },
            {
                "value": "json",
                "text": "JSON",
                "component": [
                    {
                        "value": "bat",
                        "text": "JSON-Speicher"
                    },
                    {
                        "value": "counter",
                        "text": "JSON-Zähler"
                    },
                    {
                        "value": "inverter",
                        "text": "JSON-Wechselrichter"
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
                "value": "openwb_pv_evu",
                "text": "openWB PV-Zähler am EVU-Kit",
                "component": [
                    {
                        "value": "inverter",
                        "text": "PV-Zähler"
                    }
                ]
            },
            {
                "value": "powerdog",
                "text": "Powerdog-Device",
                "component": [
                    {
                        "value": "counter",
                        "text": "Powerdog-Zähler"
                    },
                    {
                        "value": "inverter",
                        "text": "Powerdog-Wechselrichter"
                    }
                ]
            },
            {
                "value": "saxpower",
                "text": "Saxpower-Device",
                "component": [
                    {
                        "value": "bat",
                        "text": "Saxpower-Speicher"
                    }
                ]
            },
            {
                "value": "siemens",
                "text": "Siemens-Device",
                "component": [
                    {
                        "value": "bat",
                        "text": "Siemens-Speicher"
                    },
                    {
                        "value": "counter",
                        "text": "Siemens-Zähler"
                    },
                    {
                        "value": "inverter",
                        "text": "Siemens-Wechselrichter"
                    }
                ]
            },
            {
                "value": "solax",
                "text": "Solax-Device",
                "component": [
                    {
                        "value": "bat",
                        "text": "Solax-Speicher"
                    },
                    {
                        "value": "counter",
                        "text": "Solax-Zähler"
                    },
                    {
                        "value": "inverter",
                        "text": "Solax-Wechselrichter"
                    }
                ]
            },
            {
                "value": "studer",
                "text": "Studer-Device",
                "component": [
                    {
                        "value": "bat",
                        "text": "Studer-Speicher"
                    },
                    {
                        "value": "inverter",
                        "text": "Studer-Wechselrichter"
                    }
                ]
            },
            {
                "value": "sungrow",
                "text": "Sungrow-Device",
                "component": [
                    {
                        "value": "bat",
                        "text": "Sungrow-Speicher"
                    },
                    {
                        "value": "counter",
                        "text": "Sungrow-Zähler"
                    },
                    {
                        "value": "inverter",
                        "text": "Sungrow-Wechselrichter"
                    }
                ]
            },
            {
                "value": "sunny_island",
                "text": "Sunny Island-Device",
                "component": [
                    {
                        "value": "bat",
                        "text": "Sunny Island-Speicher"
                    }
                ]
            },
            {
                "value": "victron",
                "text": "Victron-Device",
                "component": [
                    {
                        "value": "bat",
                        "text": "Victron-Speicher"
                    },
                    {
                        "value": "counter",
                        "text": "Victron-Zähler"
                    },
                    {
                        "value": "inverter",
                        "text": "Victron-Wechselrichter"
                    }
                ]
            },
            {
                "value": "virtual",
                "text": "Virtuelles Modul",
                "component": [
                    {
                        "value": "counter",
                        "text": "Virtueller Zähler"
                    }
                ]
            }
        ]
        Pub().pub("openWB/set/system/configurable/devices_components", devices_components)
    except Exception:
        MainLogger().exception("Fehler im configuration-Modul")


def _pub_configurable_chargepoints() -> None:
    try:
        chargepoints = [
            {
                "value": "external_openwb",
                "text": "Externe openWB"
            },
            {
                "value": "ip_evse",
                "text": "openWB IP-EVSE"
            },
            {
                "value": "mqtt",
                "text": "MQTT-Ladepunkt"
            },
            {
                "value": "openwb_pro",
                "text": "openWB Pro"
            }
        ]
        Pub().pub("openWB/set/system/configurable/chargepoints", chargepoints)
    except Exception:
        MainLogger().exception("Fehler im configuration-Modul")
