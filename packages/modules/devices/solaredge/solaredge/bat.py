import logging
from typing import Dict, Tuple, Union, Optional

from pymodbus.constants import Endian
from dataclass_utils import dataclass_from_dict
from modules.common import modbus
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType
from modules.common.simcount import SimCounter
from modules.common.store import get_bat_value_store
from modules.devices.solaredge.solaredge.config import SolaredgeBatSetup

log = logging.getLogger(__name__)

class SolaredgeBat(AbstractBat):
    """
    Represents a SolarEdge battery.

    Handles communication with the battery via Modbus, including reading
    state, setting power limits, and activating advanced power control.
    """

    ADVANCED_PWR_CTRL_REGISTER = 57740
    COMMIT_REGISTER = 57741

    def __init__(self, device_id: int,
                 component_config: Union[Dict, SolaredgeBatSetup],
                 tcp_client: modbus.ModbusTcpClient_):
        """
        Initializes the SolaredgeBat object.

        Args:
            device_id: The device ID of the battery.
            component_config: The configuration dictionary or SolaredgeBatSetup
                object.
            tcp_client: The Modbus TCP client used for communication.
        """
        self.__device_id = device_id
        self.component_config = dataclass_from_dict(SolaredgeBatSetup,
                                                    component_config)
        self.__tcp_client = tcp_client
        self.sim_counter = SimCounter(self.__device_id,
                                        self.component_config.id,
                                        prefix="storage")
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(
            ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        """Updates the battery state by reading from Modbus."""
        self.store.set(self.read_state())

    def read_state(self) -> BatState:
        """Reads the battery state from Modbus registers.

        Returns:
            The current battery state as a BatState object.
        """
        power, soc = self.get_values()
        if soc is None or power is None:
            log.error("Invalid values read from Modbus registers.")
            return BatState(power=0, soc=0, imported=0, exported=0)
        imported, exported = self.sim_counter.sim_count(power)
        log.debug(f"Read - Power: {power}, SOC: {soc}")
        return BatState(power=power, soc=soc, imported=imported,
                        exported=exported)

    def get_values(self) -> Tuple[Optional[float], Optional[float]]:
        """Reads power and SOC values from Modbus registers.

        Returns:
            A tuple containing the power and SOC values, or None if an error
            occurs.
        Raises:
            RuntimeError: If a Modbus error occurs.
        """
        unit = self.component_config.configuration.modbus_id
        try:
            soc = self.__tcp_client.read_holding_registers(
                57732, ModbusDataType.FLOAT_32, wordorder=Endian.Little,
                unit=unit)
            power = self.__tcp_client.read_holding_registers(
                57716, ModbusDataType.FLOAT_32, wordorder=Endian.Little,
                unit=unit)
            return power, soc
        except Exception as e:
            log.error(f"Fehler beim Lesen von Modbus-Register (Unit {unit}): {e}")
            raise RuntimeError(f"Modbus-Fehler: {e}")

    def activate_advanced_power_control(self, unit: int) -> None:
        """Activates advanced power control for the battery.

        Args:
            unit: The Modbus unit ID of the battery.
        """
        try:
            current_state = self.__tcp_client.read_holding_registers(
                self.ADVANCED_PWR_CTRL_REGISTER, ModbusDataType.INT_16,
                unit=unit)
            if current_state == 1:
                log.debug("Advanced Power Control ist bereits aktiv.")
                return

            builder = modbus.BinaryPayloadBuilder(byteorder=Endian.Big,
                                                    wordorder=Endian.Little)
            builder.add_16bit_int(1)
            self.__tcp_client.write_registers(self.ADVANCED_PWR_CTRL_REGISTER,
                                            builder.to_registers(), unit=unit)
            log.debug("Advanced Power Control aktiviert.")
            self.commit_changes(unit)
        except Exception as e:
            log.error(f"Fehler beim Aktivieren von Advanced Power Control: {e}")

    def commit_changes(self, unit: int) -> None:
        """Commits changes to the battery configuration.

        Args:
            unit: The Modbus unit ID of the battery.
        """
        try:
            builder = modbus.BinaryPayloadBuilder(byteorder=Endian.Big,
                                                    wordorder=Endian.Little)
            builder.add_32bit_float(1.0)  # Value doesn't seem to matter.
            self.__tcp_client.write_registers(self.COMMIT_REGISTER,
                                            builder.to_registers(), unit=unit)
            log.debug("Changes successfully committed.")
        except Exception as e:
            log.error(f"Error committing changes: {e}")

    def set_power_limit(self, power_limit: Optional[Union[int, str]]) -> None:
        """Sets the discharge power limit for the battery.

        Args:
            power_limit: The desired power limit in Watts.  Can be an integer,
                the string "blocked", or None.  If None, the limit is set to
                5000W. If "blocked", the limit is set to 0W.

        Raises:
          ValueError: If the power limit is invalid.
        """
        discharge_limit_register = 57360
        unit = self.component_config.configuration.modbus_id

        if not self.ensure_advanced_power_control(unit): # Ensure APC is enabled.
            self.activate_advanced_power_control(unit)

        power_limit = 5000 if power_limit is None else \
            0 if str(power_limit).lower() == "blocked" else power_limit

        if not (0 <= power_limit <= 5000):
            log.error(f"Ungültiger Wert für Leistungsbegrenzung: {power_limit}. "
                      f"Muss zwischen 0 und 5000 W sein.")
            return

        try:
            current_limit = self.__tcp_client.read_holding_registers(
                discharge_limit_register, ModbusDataType.FLOAT_32, unit=unit)
            if current_limit == power_limit:
                log.info(f"Leistungsbegrenzung bereits auf {power_limit} W "
                         f"gesetzt.")
                return

            builder = modbus.BinaryPayloadBuilder(byteorder=Endian.Big,
                                                    wordorder=Endian.Little)
            builder.add_32bit_float(float(power_limit))
            self.__tcp_client.write_registers(discharge_limit_register,
                                            builder.to_registers(), unit=unit)
            log.info(f"Discharge-Limit erfolgreich auf {power_limit} W "
                     f"gesetzt.")
        except Exception as e:
            log.error(f"Fehler beim Setzen der Leistungsbegrenzung: {e}")


component_descriptor = ComponentDescriptor(
    configuration_factory=SolaredgeBatSetup)
