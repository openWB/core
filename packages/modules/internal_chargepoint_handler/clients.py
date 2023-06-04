import logging
from pathlib import Path
from typing import List, NamedTuple, Optional, Tuple, Union

from modules.common.modbus import ModbusSerialClient_
from modules.common import mpm3pm, sdm
from modules.common import evse
from modules.common import b23

log = logging.getLogger(__name__)


BUS_SOURCES = ["/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0", "/dev/serial0"]

METERS = Union[mpm3pm.Mpm3pm, sdm.Sdm630, b23.B23]
meter_config = NamedTuple("meter_config", [('type', METERS), ('modbus_id', int)])
CP0_METERS = [meter_config(mpm3pm.Mpm3pm, modbus_id=5),
              meter_config(sdm.Sdm630, modbus_id=105),
              meter_config(b23.B23, modbus_id=201)]

CP1_METERS = [meter_config(mpm3pm.Mpm3pm, modbus_id=6), meter_config(sdm.Sdm630, modbus_id=106)]

EVSE_ID = [1, 2]
EVSE_MIN_FIRMWARE = 7


class ClientConfig:
    def __init__(self, id: int, serial_client: ModbusSerialClient_) -> None:
        self.id = id
        self.serial_client = serial_client


class ClientFactory:
    def __init__(self, local_charge_point_num: int, serial_client: ModbusSerialClient_) -> None:
        self.local_charge_point_num = local_charge_point_num
        self.evse_client = self.__evse_factory(serial_client)
        self.meter_client = self.find_meter_client(CP0_METERS if self.local_charge_point_num == 0 else CP1_METERS,
                                                   serial_client)
        self._check_hardware()
        self.read_error = 0

    def __evse_factory(self, serial_client: ModbusSerialClient_) -> evse.Evse:
        for modbus_id in EVSE_ID:
            try:
                evse_client = evse.Evse(modbus_id, serial_client)
                with serial_client:
                    if evse_client.get_firmware_version() > EVSE_MIN_FIRMWARE:
                        log.debug(serial_client)
                        log.error("Modbus-ID der EVSE an LP"+str(self.local_charge_point_num)+": "+str(modbus_id))
                        return evse_client
            except Exception:
                pass
        else:
            return None

    @staticmethod
    def find_meter_client(meters: List[meter_config], serial_client: ModbusSerialClient_) -> METERS:
        for meter_type, modbus_id in meters:
            try:
                meter_client = meter_type(modbus_id, serial_client)
                with serial_client:
                    if meter_client.get_voltages()[0] > 200:
                        log.error("Verbauter Zähler: "+str(meter_type)+" mit Modbus-ID: "+str(modbus_id))
                        return meter_client
            except Exception:
                log.debug(serial_client)
                log.debug(f"Zähler {meter_type} mit Modbus-ID:{modbus_id} antwortet nicht.")
        else:
            return None

    def _check_hardware(self):
        if self.meter_client is None and self.evse_client is None:
            raise Exception("Auslesen von Zähler UND Evse nicht möglich. Vermutlich ist der USB-Adapter defekt.")
        if self.meter_client is None:
            raise Exception("Der Zähler antwortet nicht. Vermutlich ist der Zähler falsch konfiguriert oder defekt.")
        if self.evse_client is None:
            raise Exception(
                "Auslesen der EVSE nicht möglich. Vermutlich ist die EVSE defekt oder hat eine unbekannte Modbus-ID.")

    def get_pins_phase_switch(self, new_phases: int) -> Tuple[int, int]:
        # return gpio_cp, gpio_relay
        if self.local_charge_point_num == 0:
            return 22, 29 if new_phases == 1 else 37
        else:
            return 15, 11 if new_phases == 1 else 13

    def get_pins_cp_interruption(self) -> int:
        # return gpio_cp, gpio_relay
        if self.local_charge_point_num == 0:
            return 22
        else:
            return 15


def serial_client_factory(local_charge_point_num: int,
                          created_client: Optional[ModbusSerialClient_] = None) -> ModbusSerialClient_:
    tty_devices = list(Path("/dev/serial/by-path").glob("*"))
    log.debug("tty_devices"+str(tty_devices))
    resolved_devices = [str(file.resolve()) for file in tty_devices]
    log.debug("resolved_devices"+str(resolved_devices))
    counter = len(resolved_devices)
    if counter == 1 and resolved_devices[0] in BUS_SOURCES:
        if local_charge_point_num == 0:
            log.error("LP0 Device: "+str(resolved_devices[0]))
            return ModbusSerialClient_(resolved_devices[0])
        else:
            # Don't create two clients for one source!
            log.error("LP1 gleiches Device wie LP0")
            return created_client
    elif counter > 1:
        log.error("found "+str(counter)+" possible usb devices: "+str(resolved_devices))
        if local_charge_point_num == 0:
            meters = CP0_METERS
        else:
            meters = CP1_METERS
        for device in BUS_SOURCES:
            if device in resolved_devices:
                serial_client = ModbusSerialClient_(device)
                # Source immer an der Modbus-ID des Zählers fest machen, da diese immer fest ist.
                # Die USB-Anschlüsse können vertauscht sein.
                detected_device = ClientFactory.find_meter_client(meters, serial_client)
                if detected_device:
                    break
        log.error("LP"+str(local_charge_point_num)+" Device: "+str(device))
        return serial_client
