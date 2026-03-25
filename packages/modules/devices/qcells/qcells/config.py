from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class QCellsConfiguration:
    def __init__(self, modbus_id: int = 1, ip_address: Optional[str] = None, port: int = 502):
        self.modbus_id = modbus_id
        self.ip_address = ip_address
        self.port = port


class QCells:
    def __init__(self,
                 name: str = "QCells ESS",
                 type: str = "qcells",
                 id: int = 0,
                 configuration: QCellsConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or QCellsConfiguration()


class QCellsBatConfiguration:
    def __init__(self, max_power: int = 4000):
        # Maximale Lade-/Entladeleistung des Speichers in Watt.
        # Speichersteuerung via Solax Remote Control Mode 8 (Modbus).
        # Unterstuetzte Hardware: QCells Q.VOLT HYB-G3-3P (Solax Gen4),
        # Solax Gen4/Gen5/Gen6 Hybrid und AC Wechselrichter.
        # Gen2/Gen3 werden nicht unterstuetzt (kein Remote Control).
        self.max_power = max_power


class QCellsBatSetup(ComponentSetup[QCellsBatConfiguration]):
    def __init__(self,
                 name: str = "QCells Speicher",
                 type: str = "bat",
                 id: int = 0,
                 configuration: QCellsBatConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or QCellsBatConfiguration())


class QCellsCounterConfiguration:
    def __init__(self):
        pass


class QCellsCounterSetup(ComponentSetup[QCellsCounterConfiguration]):
    def __init__(self,
                 name: str = "QCells Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: QCellsCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or QCellsCounterConfiguration())


class QCellsInverterConfiguration:
    def __init__(self):
        pass


class QCellsInverterSetup(ComponentSetup[QCellsInverterConfiguration]):
    def __init__(self,
                 name: str = "QCells Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: QCellsInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or QCellsInverterConfiguration())
