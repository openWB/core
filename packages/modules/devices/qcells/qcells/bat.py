#!/usr/bin/env python3
import logging
from typing import TypedDict, Any, Optional
from pymodbus.constants import Endian

from control import data
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_bat_value_store
from modules.devices.qcells.qcells.config import QCellsBatSetup
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType

log = logging.getLogger(__name__)

# Solax/QCells Mode 1 Remote Control Registers (Holding Registers)
# Speichersteuerung via Active Power Sollwert.
REMOTE_CONTROL_MODE_REG = 0x7C           # U16: 0=Disabled, 1=Enabled Power Control
REMOTE_CONTROL_SET_TYPE_REG = 0x7D       # U16: 1=Set
REMOTE_CONTROL_ACTIVE_POWER_REG = 0x7E   # S32: Active Power Sollwert in Watt
REMOTE_CONTROL_REACTIVE_POWER_REG = 0x80  # S32: Reactive Power Sollwert (0)
REMOTE_CONTROL_DURATION_REG = 0x82       # U16: Dauer in Sekunden
REMOTE_CONTROL_TARGET_SOC_REG = 0x83     # U16: Target SoC (Dummy 0)
REMOTE_CONTROL_TARGET_ENERGY_REG = 0x84  # U32: Target Energy (Dummy 0)
REMOTE_CONTROL_TARGET_POWER_REG = 0x86   # S32: Target Charge/Discharge Power (Dummy 0)
REMOTE_CONTROL_TIMEOUT_REG = 0x88        # U16: Timeout in Sekunden

MODE_1_DISABLED = 0
MODE_1_ENABLED_POWER_CONTROL = 1
SET_TYPE_SET = 1
MIN_REMOTE_CONTROL_DURATION = 20
MIN_REMOTE_CONTROL_TIMEOUT = 60


class KwargsDict(TypedDict):
    modbus_id: int
    client: ModbusTcpClient_


class QCellsBat(AbstractBat):
    def __init__(self, component_config: QCellsBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__modbus_id: int = self.kwargs['modbus_id']
        self.client: ModbusTcpClient_ = self.kwargs['client']
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.BAT, self.component_config.id, self.fault_state)
        self.last_mode: Optional[str] = 'Undefined'

    def update(self) -> None:
        power = self.client.read_input_registers(0x0016, ModbusDataType.INT_16, unit=self.__modbus_id)
        soc = self.client.read_input_registers(0x001C, ModbusDataType.UINT_16, unit=self.__modbus_id)
        imported = self.client.read_input_registers(
            0x0021, ModbusDataType.UINT_16, unit=self.__modbus_id) * 100
        exported = self.client.read_input_registers(
            0x001D, ModbusDataType.UINT_16, unit=self.__modbus_id) * 100

        imported, exported = self.peak_filter.check_values(power, imported, exported)
        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        unit = self.__modbus_id
        log.debug(f"QCells set_power_limit: power_limit={power_limit}, "
                  f"last_mode={self.last_mode}")

        if power_limit is None:
            log.debug("Keine Batteriesteuerung, Selbstregelung durch Wechselrichter")
            if self.last_mode is not None:
                with self.client:
                    self.client.write_register(
                        REMOTE_CONTROL_MODE_REG, MODE_1_DISABLED,
                        data_type=ModbusDataType.UINT_16, unit=unit)
                self.last_mode = None
        else:
            if power_limit < 0:
                self.last_mode = 'discharge'
            elif power_limit > 0:
                self.last_mode = 'charge'
            else:
                self.last_mode = 'stop'

            ap_target = self._get_active_power_target(int(power_limit))
            self._write_mode1(ap_target, unit=unit)

    def _get_active_power_target(self, power_limit: int) -> int:
        # openWB-Werte verwenden (nicht WR-Berechnungen):
        # power_limit < 0 = Entladen, 0 = Stop, > 0 = Laden
        home_consumption = int(data.data.counter_all_data.data.set.home_consumption)
        cp_power = int(data.data.cp_all_data.data.get.power)
        house_load = max(0, home_consumption + cp_power)
        pv_generation = max(0, int(data.data.pv_all_data.data.get.power * -1))
        # Mode 1 / Enabled Battery Control: house_load wird inverter-intern bereits berücksichtigt.
        ap_target = power_limit - pv_generation

        try:
            evu_counter = data.data.counter_all_data.get_evu_counter()
            import_limit = int(evu_counter.data.config.max_total_power)
        except Exception:
            import_limit = 0

        import_bound = None
        if import_limit > 0 and ap_target > 0:
            import_bound = import_limit - house_load
            ap_target = min(ap_target, import_bound)

        log.debug((
            f"QCells Mode1 target: power_limit={power_limit}W, home_consumption={home_consumption}W, "
            f"cp_power={cp_power}W, house_load={house_load}W, "
            f"pv_generation={pv_generation}W, import_limit={import_limit}W, "
            f"import_bound={import_bound}W -> ap_target={ap_target}W"
        ))
        return int(ap_target)

    def _write_mode1(self, ap_target: int, unit: int) -> None:
        """Schreibt die Mode 1 Remote Control Register (0x7C-0x88)."""
        duration, timeout = self._get_mode1_timing()
        log.debug((
            f"QCells Mode1 write: mode={MODE_1_ENABLED_POWER_CONTROL}, set_type={SET_TYPE_SET}, "
            f"active_power={ap_target}W, reactive_power=0var, duration={duration}s, "
            f"target_soc=0, target_energy=0Wh, target_power=0W, timeout={timeout}s"
        ))
        with self.client:
            self.client.write_register(
                REMOTE_CONTROL_MODE_REG, MODE_1_ENABLED_POWER_CONTROL,
                data_type=ModbusDataType.UINT_16, unit=unit)
            self.client.write_register(
                REMOTE_CONTROL_SET_TYPE_REG, SET_TYPE_SET,
                data_type=ModbusDataType.UINT_16, unit=unit)
            self.client.write_register(
                REMOTE_CONTROL_ACTIVE_POWER_REG, ap_target,
                data_type=ModbusDataType.INT_32, wordorder=Endian.Little, unit=unit)
            self.client.write_register(
                REMOTE_CONTROL_REACTIVE_POWER_REG, 0,
                data_type=ModbusDataType.INT_32, wordorder=Endian.Little, unit=unit)
            self.client.write_register(
                REMOTE_CONTROL_DURATION_REG, duration,
                data_type=ModbusDataType.UINT_16, unit=unit)
            self.client.write_register(
                REMOTE_CONTROL_TARGET_SOC_REG, 0,
                data_type=ModbusDataType.UINT_16, unit=unit)
            self.client.write_register(
                REMOTE_CONTROL_TARGET_ENERGY_REG, 0,
                data_type=ModbusDataType.UINT_32, wordorder=Endian.Little, unit=unit)
            self.client.write_register(
                REMOTE_CONTROL_TARGET_POWER_REG, 0,
                data_type=ModbusDataType.INT_32, wordorder=Endian.Little, unit=unit)
            self.client.write_register(
                REMOTE_CONTROL_TIMEOUT_REG, timeout,
                data_type=ModbusDataType.UINT_16, unit=unit)

    def _get_mode1_timing(self) -> tuple[int, int]:
        try:
            control_interval = int(data.data.general_data.data.control_interval)
        except Exception:
            control_interval = 10

        duration = max(MIN_REMOTE_CONTROL_DURATION, control_interval * 2)
        timeout = max(MIN_REMOTE_CONTROL_TIMEOUT, control_interval * 3)
        return duration, timeout

    def power_limit_controllable(self) -> bool:
        return True


component_descriptor = ComponentDescriptor(configuration_factory=QCellsBatSetup)
