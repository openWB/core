from typing import Dict, List
import sys

try:
    from ...helpermodules import log
    from ..common import modbus
    from ..common.abstract_device import AbstractDevice, DeviceUpdater
    from ..common.abstract_component import ComponentUpdater
    from . import bat
    from . import counter
    from . import inverter
except (ImportError, ValueError, SystemError):
    from helpermodules import log
    from modules.common import modbus
    from modules.common.abstract_device import AbstractDevice, DeviceUpdater
    from modules.common.abstract_component import ComponentUpdater
    import bat
    import counter
    import inverter


def get_default_config() -> dict:
    return {
        "name": "MQTT",
        "type": "mqtt",
        "id": 0,
        "configuration": {
        }
    }


COMPONENT_TYPE_TO_MODULE = {
    "bat": bat,
    "counter": counter,
    "inverter": inverter
}


class Device(AbstractDevice):
    COMPONENT_TYPE_TO_CLASS = {
        "bat": bat.MqttBat,
        "counter": counter.MqttCounter,
        "inverter": inverter.MqttInverter
    }
    _components = {}  # type: Dict[str, ComponentUpdater]

    def __init__(self, device_config: dict) -> None:
        try:
            self.device_config = device_config
            self.client = None
        except Exception:
            log.MainLogger().exception("Fehler im Modul " +
                                       device_config["name"])

    def add_component(self, component_config: dict):
        factory = COMPONENT_TYPE_TO_MODULE[component_config["type"]].create_component
        self._components["component"+str(component_config["id"])
                         ] = factory(self.device_config, component_config, self.client)

    def get_values(self):
        log.MainLogger().debug("Mqtt-Module müssen nicht gelesen werden.")


def read_legacy(argv: List[str]):
    """ Ausführung des Moduls als Python-Skript
    """

    log.MainLogger().debug('Start reading mqtt')
    component_type = argv[1]
    try:
        num = int(argv[2])
    except IndexError:
        num = None

    device_config = get_default_config()
    dev = DeviceUpdater(Device((device_config)))
    if component_type in COMPONENT_TYPE_TO_MODULE:
        component_config = COMPONENT_TYPE_TO_MODULE[
            component_type].get_default_config()
    else:
        raise Exception("illegal component type " + component_type +
                        ". Allowed values: " +
                        ','.join(COMPONENT_TYPE_TO_MODULE.keys()))

    component_config["id"] = num
    component_config["configuration"]["id"] = id
    dev.device.add_component(component_config)

    log.MainLogger().debug('mqtt Device')

    dev.get_values()


if __name__ == "__main__":
    try:
        read_legacy(sys.argv)
    except Exception:
        log.MainLogger().exception("Fehler im Modul openwb_flex")
