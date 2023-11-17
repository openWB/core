import logging
from pathlib import Path
from typing import List, NamedTuple, Optional, Tuple, Union

from modules.common.modbus import ModbusSerialClient_, ModbusTcpClient_
from modules.common import mpm3pm, sdm
from modules.common import evse
from modules.common import b23

log = logging.getLogger(__name__)


BUS_SOURCES = ("/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0", "/dev/serial0")

METERS = Union[mpm3pm.Mpm3pm, sdm.Sdm630, b23.B23]
meter_config = NamedTuple("meter_config", [('type', METERS), ('modbus_id', int)])
CP0_METERS = [meter_config(mpm3pm.Mpm3pm, modbus_id=5),
              meter_config(sdm.Sdm630, modbus_id=105),
              meter_config(b23.B23, modbus_id=201)]

CP1_METERS = [meter_config(mpm3pm.Mpm3pm, modbus_id=6), meter_config(sdm.Sdm630, modbus_id=106)]

EVSE_ID_CP0 = [1]
EVSE_ID_TWO_BUSSES_CP1 = [1, 2]
EVSE_ID_ONE_BUS_CP1 = [2]
EVSE_MIN_FIRMWARE = 7


class ClientHandler:
    def __init__(self,
                 local_charge_point_num: int,
                 client: Union[ModbusSerialClient_, ModbusTcpClient_],
                 evse_ids: List[int]) -> None:
        self.client = client
        self.local_charge_point_num = local_charge_point_num
        self.evse_client = self._evse_factory(client, evse_ids)
        self.meter_client = self.find_meter_client(CP0_METERS if self.local_charge_point_num == 0 else CP1_METERS,
                                                   client)
        self.check_hardware()
        self.read_error = 0

    def _evse_factory(self, client: Union[ModbusSerialClient_, ModbusTcpClient_], evse_ids: List[int]) -> evse.Evse:
        for modbus_id in evse_ids:
            evse_client = evse.Evse(modbus_id, client)
            with client:
                try:
                    if evse_client.get_firmware_version() > EVSE_MIN_FIRMWARE:
                        log.debug(client)
                        log.error("Modbus-ID der EVSE an LP"+str(self.local_charge_point_num)+": "+str(modbus_id))
                        return evse_client
                except Exception:
                    pass
        else:
            return None

    @staticmethod
    def find_meter_client(meters: List[meter_config], client: Union[ModbusSerialClient_, ModbusTcpClient_]) -> METERS:
        for meter_type, modbus_id in meters:
            meter_client = meter_type(modbus_id, client)
            with client:
                try:
                    if meter_client.get_voltages()[0] > 200:
                        log.error("Verbauter Zähler: "+str(meter_type)+" mit Modbus-ID: "+str(modbus_id))
                        return meter_client
                except Exception:
                    log.debug(client)
                    log.debug(f"Zähler {meter_type} mit Modbus-ID:{modbus_id} antwortet nicht.")
        else:
            return None
    OPEN_TICKET = " Bitte nehme über die Support-Funktion in den Einstellungen Kontakt mit uns auf."
    USB_ADAPTER_BROKEN = ("Auslesen von Zähler UND Evse nicht möglich. "
                          f"Vermutlich ist der USB-Adapter defekt. {OPEN_TICKET}")
    METER_PROBLEM = ("Der Zähler konnte nicht ausgelesen werden. "
                     f"Vermutlich ist der Zähler falsch konfiguriert oder defekt. {OPEN_TICKET}")
    METER_BROKEN = ("Die Spannungen des Zählers konnten nicht korrekt ausgelesen werden. "
                    f"Der Zähler ist defekt. {OPEN_TICKET}")
    EVSE_BROKEN = ("Auslesen der EVSE nicht möglich. "
                   f"Vermutlich ist die EVSE defekt oder hat eine unbekannte Modbus-ID. {OPEN_TICKET}")

    def check_hardware(self):
        try:
            if self.evse_client.get_firmware_version() > EVSE_MIN_FIRMWARE:
                evse_check_passed = True
            else:
                evse_check_passed = False
        except Exception:
            evse_check_passed = False
        meter_check_passed, meter_error_msg = self.check_meter()
        if meter_check_passed is False and evse_check_passed is False:
            raise Exception(self.USB_ADAPTER_BROKEN)
        if meter_check_passed is False:
            raise Exception(meter_error_msg)
        if meter_error_msg == self.METER_BROKEN:
            log.error(self.METER_BROKEN)
        if evse_check_passed is False:
            raise Exception(self.EVSE_BROKEN)

    def check_meter(self):
        def valid_voltage(voltage) -> bool:
            return 200 < voltage < 250
        try:
            voltages = self.meter_client.get_voltages()
            if ((valid_voltage(voltages[0]) and voltages[1] == 0 and voltages[2] == 0) or
                    (valid_voltage(voltages[0]) and valid_voltage(voltages[1]) and voltages[2] == 0) or
                    (valid_voltage(voltages[0]) and valid_voltage(voltages[1]) and valid_voltage((voltages[2])))):
                return True, None
            else:
                return True, self.METER_BROKEN
        except Exception:
            return False, self.METER_PROBLEM

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


def client_factory(local_charge_point_num: int,
                   created_client_handler: Optional[ClientHandler] = None) -> ClientHandler:
    tty_devices = list(Path("/dev/serial/by-path").glob("*"))
    log.debug("tty_devices"+str(tty_devices))
    resolved_devices = [str(file.resolve()) for file in tty_devices]
    log.debug("resolved_devices"+str(resolved_devices))
    counter = len(resolved_devices)
    if counter == 0:
        # Wenn kein USB-Gerät gefunden wird, wird der Modbus-Anschluss der AddOn-Platine genutzt (/dev/serial0)
        serial_client = ModbusSerialClient_("/dev/serial0")
        if local_charge_point_num == 0:
            evse_ids = EVSE_ID_CP0
        else:
            evse_ids = EVSE_ID_ONE_BUS_CP1
    elif counter == 1 and resolved_devices[0] in BUS_SOURCES:
        if local_charge_point_num == 0:
            log.error("LP0 Device: "+str(resolved_devices[0]))
            serial_client = ModbusSerialClient_(resolved_devices[0])
            evse_ids = EVSE_ID_CP0
        else:
            # Don't create two clients for one source!
            log.error("LP1 gleiches Device wie LP0")
            serial_client = created_client_handler.client
            evse_ids = EVSE_ID_ONE_BUS_CP1
    elif counter > 1:
        log.error("found "+str(counter)+" possible usb devices: "+str(resolved_devices))
        if local_charge_point_num == 0:
            meters = CP0_METERS
            evse_ids = EVSE_ID_CP0
        else:
            meters = CP1_METERS
            evse_ids = EVSE_ID_TWO_BUSSES_CP1
        for device in BUS_SOURCES:
            if device in resolved_devices:
                serial_client = ModbusSerialClient_(device)
                # Source immer an der Modbus-ID des Zählers fest machen, da diese immer fest ist.
                # Die USB-Anschlüsse können vertauscht sein.
                detected_device = ClientHandler.find_meter_client(meters, serial_client)
                if detected_device:
                    break
        log.error("LP"+str(local_charge_point_num)+" Device: "+str(device))
    return ClientHandler(local_charge_point_num, serial_client, evse_ids)
