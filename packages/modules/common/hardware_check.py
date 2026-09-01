import logging
import time
import pymodbus
from typing import Any, Optional, Protocol, Tuple, Union

from modules.common.component_state import CounterState, EvseState
from modules.common.evse import Evse
from modules.common.fault_state import FaultState
from modules.common.modbus import ModbusSerialClient_, ModbusTcpClient_

log = logging.getLogger(__name__)


EVSE_MIN_FIRMWARE = 7
MAX_ATTEMPTS = 3
RETRY_DELAY_SECONDS = 0.3

READ_RS485_ADAPTER_AGAIN = "Erneutes Auslesen des {}"
READ_USB_ADAPTER_AGAIN = READ_RS485_ADAPTER_AGAIN.format('USB-Adapters')
READ_LAN_ADAPTER_AGAIN = READ_RS485_ADAPTER_AGAIN.format('LAN-Konverters')
METER_PROBLEM = "Erneutes Auslesen des Zählers"
READ_METER_VOLTAGES_AGAIN = "Erneutes Auslesen der Spannungen am Zähler: {}V"
METER_NO_SERIAL_NUMBER = ("Die Seriennummer des Zählers für das Ladelog kann nicht ausgelesen werden. Wenn Du die "
                          "Seriennummer für Abrechnungszwecke benötigst, wende Dich bitte an unseren Support. Die "
                          "Funktionalität wird dadurch nicht beeinträchtigt!")
READ_EVSE_AGAIN = "Erneutes Auslesen der EVSE"


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
        return READ_METER_VOLTAGES_AGAIN.format(voltages)
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
        evse_check_passed = False
        evse_state: EvseState
        # 2x Retry bei EVSE-Auslesen vor dem Absetzen einer Fehlermeldung
        try:
            with self.client:
                for attempt in range(MAX_ATTEMPTS):
                    try:
                        evse_state = self.evse_client.get_evse_state()
                        evse_check_passed = True
                        break
                    except (pymodbus.exceptions.ModbusIOException,
                            pymodbus.exceptions.ConnectionException) as e:
                        evse_check_passed = self.handle_exception(e)
                        # nur warten, wenn danach noch ein Versuch folgt
                        if attempt < MAX_ATTEMPTS - 1 and evse_check_passed is False:
                            time.sleep(RETRY_DELAY_SECONDS)
        except Exception as e:
            evse_check_passed = self.handle_exception(e)
        meter_check_passed, meter_error_msg, counter_state = self.check_meter()
        if meter_check_passed is False and evse_check_passed is False:
            if isinstance(self.client, ModbusTcpClient_):
                raise Exception(READ_LAN_ADAPTER_AGAIN)
            else:
                raise Exception(READ_USB_ADAPTER_AGAIN)
        if meter_check_passed is False:
            if evse_check_passed is False:
                if isinstance(self.client, ModbusTcpClient_):
                    raise Exception(READ_LAN_ADAPTER_AGAIN)
                else:
                    raise Exception(READ_USB_ADAPTER_AGAIN)
            else:
                raise Exception(meter_error_msg)
        elif evse_check_passed and meter_check_passed and meter_error_msg is not None:
            fault_state.warning(meter_error_msg)
        if evse_check_passed is False:
            if meter_error_msg is not None:
                raise Exception(f"{READ_EVSE_AGAIN} {meter_error_msg}")
            else:
                raise Exception(READ_EVSE_AGAIN)
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
