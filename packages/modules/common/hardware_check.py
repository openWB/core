import pymodbus
from typing import Any, List, Optional, Protocol, Tuple, Union

from modules.common.evse import Evse
from modules.common.fault_state import FaultState
from modules.common.modbus import ModbusSerialClient_, ModbusTcpClient_

EVSE_MIN_FIRMWARE = 7

OPEN_TICKET = (" Bitte nehme bei anhaltenden Problemen über die Support-Funktion in den Einstellungen Kontakt mit " +
               "uns auf.")
RS485_ADPATER_BROKEN = ("Auslesen von Zähler UND Evse nicht möglich. Vermutlich ist {} defekt oder zwei "
                        f"Busteilnehmer haben die gleiche Modbus-ID. Bitte die Zähler-ID prüfen. {OPEN_TICKET}")
USB_ADAPTER_BROKEN = RS485_ADPATER_BROKEN.format('der USB-Adapter')
LAN_ADAPTER_BROKEN = (f"{RS485_ADPATER_BROKEN.format('der LAN-Konverter abgestürzt,')} "
                      "Bitte den openWB series2 satellit stromlos machen.")
METER_PROBLEM = ("Der Zähler konnte nicht ausgelesen werden. "
                 f"Vermutlich ist der Zähler falsch konfiguriert oder defekt. {OPEN_TICKET}")
METER_BROKEN = ("Die Spannungen des Zählers konnten nicht korrekt ausgelesen werden. "
                f"Der Zähler ist defekt. {OPEN_TICKET}")
EVSE_BROKEN = ("Auslesen der EVSE nicht möglich. "
               f"Vermutlich ist die EVSE defekt oder hat eine unbekannte Modbus-ID. {OPEN_TICKET}")


def check_meter_values(voltages: List[float]) -> Optional[str]:
    def valid_voltage(voltage) -> bool:
        return 200 < voltage < 250
    if ((valid_voltage(voltages[0]) and voltages[1] == 0 and voltages[2] == 0) or
            (valid_voltage(voltages[0]) and valid_voltage(voltages[1]) and voltages[2] == 0) or
            (valid_voltage(voltages[0]) and valid_voltage(voltages[1]) and valid_voltage((voltages[2])))):
        return None
    else:
        return METER_BROKEN


class ClientHandlerProtocol(Protocol):
    @property
    def client(self) -> Union[ModbusSerialClient_, ModbusTcpClient_]: ...
    @property
    def local_charge_point_num(self) -> int: ...
    @property
    def fault_state(self) -> FaultState: ...
    @property
    def evse_client(self) -> Evse: ...
    @property
    def meter_client(self) -> Any: ...
    @property
    def read_error(self) -> int: ...


class SeriesHardwareCheckMixin:
    def __init__(self) -> None:
        pass

    def handle_exception(self: ClientHandlerProtocol, exception: Exception):
        # separated for test purposes
        if (isinstance(self.client, ModbusTcpClient_) and
                isinstance(exception, pymodbus.exceptions.ConnectionException)):
            raise exception
        else:
            return False

    def check_hardware(self: ClientHandlerProtocol):

        try:
            if self.evse_client.get_firmware_version() > EVSE_MIN_FIRMWARE:
                evse_check_passed = True
            else:
                evse_check_passed = False
        except Exception as e:
            evse_check_passed = self.handle_exception(e)
        meter_check_passed, meter_error_msg = self.check_meter()
        if meter_check_passed is False and evse_check_passed is False:
            if isinstance(self.client, ModbusTcpClient_):
                raise Exception(LAN_ADAPTER_BROKEN)
            else:
                raise Exception(USB_ADAPTER_BROKEN)
        if meter_check_passed is False:
            raise Exception(meter_error_msg)
        elif meter_check_passed and meter_error_msg == METER_BROKEN:
            self.fault_state.warning(METER_BROKEN)
        if evse_check_passed is False:
            raise Exception(EVSE_BROKEN)

    def check_meter(self: ClientHandlerProtocol) -> Tuple[bool, Optional[str]]:
        try:
            return True, check_meter_values(self.meter_client.get_voltages())
        except Exception:
            return False, METER_PROBLEM
