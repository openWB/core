import logging
import time
import datetime

from dataclasses import dataclass

from modules.common import modbus
from modules.common.sdm import Sdm120

log = logging.getLogger(__name__)


@dataclass
class SocketMeterData:
    imported_wh: float = None
    exported_wh: float = None
    current: float = None
    voltage: float = None
    power: float = None
    power_factor: float = None
    serial: str = None
    model: str = None
    last_update: str = None


class SocketMeterHandler:
    def __init__(self, client: modbus.ModbusClient) -> None:
        self._client = client
        self._meter = Sdm120(modbus_id=9, client=self._client)
        self.data = SocketMeterData()

    def update(self):

        # NOTE: Standard socket is always assumed single-phase and hence we always take the first element
        # of 3-phase meter readings (currents, voltages, power-factors)

        self.data.imported_wh = self._meter.get_imported()
        # log.info(f"standard-socket: imported: {self.data.imported_wh}")

        self.data.current = self._meter.get_currents()[0]
        # log.info(f"standard-socket: currents: {self.data.currents}")
        time.sleep(0.1)

        self.data.voltage = self._meter.get_voltages()[0]
        # log.info(f"standard-socket: voltages: {self.data.voltages}")
        time.sleep(0.1)

        self.data.power = self._meter.get_power()[1]
        # log.info(f"standard-socket: power: {self.data.power}")
        time.sleep(0.1)

        self.data.power_factor = self._meter.get_power_factors()[0]
        # log.info(f"standard-socket: power_factors: {self.data.power_factors}")
        time.sleep(0.1)

        self.data.exported_wh = self._meter.get_exported()
        # log.info(f"standard-socket: exported: {self.data.exported_wh}")

        # frequency is currently not needed (it's sufficient to check it from EV meter)
        # self.data.frequency = self._meter.get_frequency()
        # log.info(f"standard-socket: frequency: {self.data.frequency}")

        if self.data.serial is None:
            self.data.serial = self._meter.get_serial_number()

        if self.data.model is None:
            self.data.model = self._meter.get_model()

        self.data.last_update = f"{datetime.datetime.now(datetime.timezone.utc).isoformat()}Z"
