import logging
import pymodbus
from typing import Any, Optional, Protocol, Tuple, Union

from modules.common.component_state import CounterState, EvseState
from modules.common.evse import Evse
from modules.common.fault_state import FaultState
from modules.common.modbus import ModbusSerialClient_, ModbusTcpClient_

log = logging.getLogger(__name__)


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
EVSE_BROKEN = "Auslesen der EVSE nicht möglich. Vermutlich ist die EVSE defekt oder hat eine unbekannte Modbus-ID. "


def check_meter_values(counter_state: CounterState, fault_state: Optional[FaultState] = None) -> None:
    meter_msg = _check_meter_values(counter_state)
    if fault_state and meter_msg:
        fault_state.warning(meter_msg)


def _check_meter_values(counter_state: CounterState) -> Optional[str]:
    # Nur prüfen, dass keine Phase ausgefallen ist
    # Es gibt einige Fälle, in denen die Normtoleranzen der Netzspannung nicht eingehalten werden, aber kein Defekt
    # vorliegt und der Kunde nicht eingreifen muss. Dann soll keine Warnung angezeigt werden.
    # Kona 1-phasig induziert auf L2 40V, Zoe auf L2 130V
    # beim Ladestart sind Strom und Spannung nicht immer konsistent.
    voltages = counter_state.voltages
    if (voltages[1] == 0 and voltages[2] > 30) or voltages[0] == 0:
        return METER_BROKEN_VOLTAGES.format(voltages)
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
            fault_state.warning(meter_error_msg + OPEN_TICKET)
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
                log.warning(METER_NO_SERIAL_NUMBER)
            return True, _check_meter_values(counter_state), counter_state
        except Exception:
            return False, METER_PROBLEM, None
