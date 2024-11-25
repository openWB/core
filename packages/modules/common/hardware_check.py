import pymodbus
from typing import Any, List, Optional, Protocol, Tuple, Union

from modules.common.evse import Evse
from modules.common.fault_state import FaultState
from modules.common.modbus import ModbusSerialClient_, ModbusTcpClient_

EVSE_MIN_FIRMWARE = 7

OPEN_TICKET = (" Bitte nehme bei anhaltenden Problemen über die Support-Funktion in den Einstellungen Kontakt mit " +
               "uns auf.")
RS485_ADAPTER_BROKEN = ("Auslesen von Zähler UND Evse nicht möglich. Vermutlich ist {} defekt oder zwei "
                        "Busteilnehmer haben die gleiche Modbus-ID. Bitte die Zähler-ID prüfen.")
USB_ADAPTER_BROKEN = RS485_ADAPTER_BROKEN.format('der USB-Adapter')
LAN_ADAPTER_BROKEN = (f"{RS485_ADAPTER_BROKEN.format('der LAN-Konverter abgestürzt,')} "
                      "Bitte den openWB series2 satellit stromlos machen.")
METER_PROBLEM = "Der Zähler konnte nicht ausgelesen werden. Vermutlich ist der Zähler falsch konfiguriert oder defekt."
METER_BROKEN = "Die Spannungen des Zählers konnten nicht korrekt ausgelesen werden: {}V Der Zähler ist defekt."
METER_NO_SERIAL_NUMBER = ("Die Seriennummer des Zählers für das Ladelog kann nicht ausgelesen werden. Wenn Sie die "
                          "Seriennummer für Abrechnungszwecke benötigen, wenden Sie sich bitte an unseren Support. Die "
                          "Funktionalität wird dadurch nicht beeinträchtigt!")
EVSE_BROKEN = "Auslesen der EVSE nicht möglich. Vermutlich ist die EVSE defekt oder hat eine unbekannte Modbus-ID."


def check_meter_values(voltages: List[float]) -> Optional[str]:
    def valid_voltage(voltage) -> bool:
        return 200 < voltage < 260
    if ((valid_voltage(voltages[0]) and voltages[1] == 0 and voltages[2] == 0) or
            # Zoe lädt einphasig an einphasiger Wallbox und erzeugt Spannung auf L2 (ca 126V)
            (valid_voltage(voltages[0]) and 115 < voltages[1] < 135 and voltages[2] == 0) or
            (valid_voltage(voltages[0]) and valid_voltage(voltages[1]) and voltages[2] == 0) or
            (valid_voltage(voltages[0]) and valid_voltage(voltages[1]) and valid_voltage((voltages[2])))):
        return None
    else:
        return METER_BROKEN.format(voltages)


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

    def check_hardware(self: ClientHandlerProtocol, fault_state: FaultState):

        try:
            if self.evse_client.get_firmware_version() > EVSE_MIN_FIRMWARE:
                evse_check_passed = True
            else:
                evse_check_passed = False
        except Exception as e:
            evse_check_passed = self.handle_exception(e)
        meter_check_passed, meter_error_msg = self.check_meter()
        if meter_check_passed is False:
            if evse_check_passed is False:
                if isinstance(self.client, ModbusTcpClient_):
                    raise Exception(LAN_ADAPTER_BROKEN + OPEN_TICKET)
                else:
                    raise Exception(USB_ADAPTER_BROKEN + OPEN_TICKET)
            else:
                raise Exception(meter_error_msg + OPEN_TICKET)
        elif evse_check_passed and meter_check_passed and meter_error_msg is not None:
            if meter_error_msg != METER_NO_SERIAL_NUMBER:
                meter_error_msg += OPEN_TICKET
            fault_state.warning(meter_error_msg)
        if evse_check_passed is False:
            if meter_error_msg is not None:
                raise Exception(EVSE_BROKEN + " " + meter_error_msg + OPEN_TICKET)
            else:
                raise Exception(EVSE_BROKEN + OPEN_TICKET)

    def check_meter(self: ClientHandlerProtocol) -> Tuple[bool, Optional[str]]:
        try:
            serial_number = self.meter_client.get_serial_number()
            if serial_number == "0" or serial_number is None:
                return True, METER_NO_SERIAL_NUMBER
            return True, check_meter_values(self.meter_client.get_voltages())
        except Exception:
            return False, METER_PROBLEM
