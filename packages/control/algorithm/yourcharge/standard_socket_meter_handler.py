import logging
import time
from typing import List

from dataclasses import dataclass

from modules.common import modbus
from modules.common.sdm import Sdm120

log = logging.getLogger(__name__)

@dataclass
class SocketMeterData:
    imported_wh: float = None
    exported_wh: float = None
    currents: List[float] = None
    voltages: List[float] = None
    power: float = None
    power_factors: List[float] = None
    serial: str = None
    model: str = None

class SocketMeterHandler:
    def __init__(self, client: modbus.ModbusClient) -> None:
        self._client = client
        self._meter = Sdm120(modbus_id=9, client=self._client)
        self.data = SocketMeterData()

    def update(self):
        self.data.imported_wh = self._meter.get_imported()
        # log.info(f"standard-socket: imported: {self.data.imported_wh}")

        self.data.currents = self._meter.get_currents()
        # log.info(f"standard-socket: currents: {self.data.currents}")
        time.sleep(0.1)

        self.data.voltages = self._meter.get_voltages()
        # log.info(f"standard-socket: voltages: {self.data.voltages}")
        time.sleep(0.1)

        self.data.power = self._meter.get_power()[1]
        # log.info(f"standard-socket: power: {self.data.power}")
        time.sleep(0.1)

        self.data.power_factors = self._meter.get_power_factors()
        # log.info(f"standard-socket: power_factors: {self.data.power_factors}")
        time.sleep(0.1)

        self.data.exported_wh = self._meter.get_exported()
        # log.info(f"standard-socket: exported: {self.data.exported_wh}")

        # frequency is currently not needed (it's sufficient to check it from EV meter)
        # self.data.frequency = self._meter.get_frequency()
        # log.info(f"standard-socket: frequency: {self.data.frequency}")

        if self.data.serial is None:
            self.data.serial = self._meter.get_serial()

        if self.data.model is None:
            self.data.model = self._meter.get_model()