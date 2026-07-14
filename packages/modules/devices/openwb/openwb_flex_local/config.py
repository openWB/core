from ..vendor import vendor_descriptor
from modules.common.component_setup import ComponentSetup
from modules.common.serial_modbus_devices import get_serial_modbus_devices, BUS_SOURCES
import logging
log = logging.getLogger(__name__)


class FlexLocalConfiguration:
    def __init__(self) -> None:
        device, count = get_serial_modbus_devices()
        if count == 1 and device[0] in BUS_SOURCES:
            self.port = device[0]
            log.debug(f"Verbrauchszähler mit lokaler Auslesung nutzt Port {self.port}")
        else:
            self.port = "UNKNOWN"
            log.debug(f"Verbrauchszähler mit lokaler Auslesung konnte Port nicht ermitteln, gefundene Ports: {device}")


class FlexLocalSetup:
    def __init__(self,
                 name: str = "Verbrauchszähler mit lokaler Auslesung",
                 type: str = "openwb_flex_local",
                 id: int = 0,
                 configuration: FlexLocalConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or FlexLocalConfiguration()


class LocalConsumptionCounterConfiguration:
    def __init__(self, id: int = 1, type: str = "sdm630") -> None:
        self.id = id
        self.type = type


class LocalConsumptionCounterSetup(ComponentSetup[LocalConsumptionCounterConfiguration]):
    def __init__(self,
                 name: str = "openWB Lokaler Verbrauchszähler",
                 type: str = "consumption_counter",
                 id: int = 0,
                 configuration: LocalConsumptionCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or LocalConsumptionCounterConfiguration())
