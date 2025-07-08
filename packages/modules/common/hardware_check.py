import pymodbus
from typing import Any, Optional, Protocol, Tuple, Union

from modules.common.component_state import CounterState, EvseState
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
METER_BROKEN_VOLTAGES = "Die Spannungen des Zählers konnten nicht korrekt ausgelesen werden: {}V Der Zähler ist defekt."
METER_NO_SERIAL_NUMBER = ("Die Seriennummer des Zählers für das Ladelog kann nicht ausgelesen werden. Wenn Sie die "
                          "Seriennummer für Abrechnungszwecke benötigen, wenden Sie sich bitte an unseren Support. Die "
                          "Funktionalität wird dadurch nicht beeinträchtigt!")
EVSE_BROKEN = ("Auslesen der EVSE nicht möglich. Vermutlich ist die EVSE defekt oder hat eine unbekannte Modbus-ID. "
               "(Fehlermeldung nur relevant, wenn diese auf der Startseite oder im Status angezeigt wird.)")
METER_IMPLAUSIBLE_VALUE = ("Der Zähler hat einen unplausiblen Wert zurückgegeben: Leistungen {}W, Ströme {}A, "
                           "Spannungen {}V.")


def check_meter_values(counter_state: CounterState, fault_state: Optional[FaultState] = None) -> None:
    meter_msg = _check_meter_values(counter_state)
    if fault_state and meter_msg:
        fault_state.warning(meter_msg)


def _check_meter_values(counter_state: CounterState) -> Optional[str]:
    def valid_voltage(voltage) -> bool:
        return 200 < voltage < 250
    voltages = counter_state.voltages
    if not ((valid_voltage(voltages[0]) and voltages[1] == 0 and voltages[2] == 0) or
            # Zoe lädt einphasig an einphasiger Wallbox und erzeugt Spannung auf L2 (ca 126V)
            (valid_voltage(voltages[0]) and 115 < voltages[1] < 135 and voltages[2] == 0) or
            (valid_voltage(voltages[0]) and valid_voltage(voltages[1]) and voltages[2] == 0) or
            (valid_voltage(voltages[0]) and valid_voltage(voltages[1]) and valid_voltage((voltages[2])))):
        return METER_BROKEN_VOLTAGES.format(voltages)
    interdependent_values = [sum(counter_state.currents), counter_state.power]
    if not (all(v < 0.5 for v in interdependent_values) or all(v > 0.5 for v in interdependent_values)):
        return METER_IMPLAUSIBLE_VALUE.format(counter_state.powers, counter_state.currents, counter_state.voltages)
    return None


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
    @property
    def handle_exception(self, exception: Exception) -> bool: ...
    @property
    def request_and_check_hardware(self, fault_state: FaultState) -> Tuple[EvseState, CounterState]: ...
    @property
    def check_meter(self) -> Tuple[bool, Optional[str], CounterState]: ...


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

    def request_and_check_hardware(self: ClientHandlerProtocol,
                                   fault_state: FaultState) -> Tuple[EvseState, CounterState]:
        try:
            with self.client:
                evse_state = self.evse_client.get_evse_state()
            evse_check_passed = True
        except Exception as e:
            evse_check_passed = self.handle_exception(e)
        meter_check_passed, meter_error_msg, counter_state = self.check_meter()
        if meter_check_passed is False and evse_check_passed is False:
            if isinstance(self.client, ModbusTcpClient_):
                raise Exception(LAN_ADAPTER_BROKEN)
            else:
                raise Exception(USB_ADAPTER_BROKEN)
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
        return evse_state, counter_state

    def check_meter(self: ClientHandlerProtocol) -> Tuple[bool, Optional[str], CounterState]:
        try:
            with self.client:
                counter_state = self.meter_client.get_counter_state()
            if counter_state.serial_number == "0" or counter_state.serial_number is None:
                return True, METER_NO_SERIAL_NUMBER, counter_state
            return True, _check_meter_values(counter_state), counter_state
        except Exception:
            return False, METER_PROBLEM, None
