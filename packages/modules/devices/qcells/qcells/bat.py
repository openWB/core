#!/usr/bin/env python3
import logging
from typing import TypedDict, Any, Optional

from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_bat_value_store
from modules.devices.qcells.qcells.config import QCellsBatSetup

log = logging.getLogger(__name__)

# Solax/QCells Mode 8 Remote Control Registers (Holding Registers)
# Speichersteuerung via "Individual Setting - Duration Mode"
# Unterstuetzte Hardware: QCells Q.VOLT HYB-G3-3P (Solax Gen4),
# Solax Gen4/Gen5/Gen6 Hybrid und AC Wechselrichter.
REMOTE_CONTROL_MODE_REG = 0xA0           # U16: 0=Disabled, 8=Individual Duration
REMOTE_CONTROL_SET_TYPE_REG = 0xA1       # U16: 1=Set
REMOTE_CONTROL_PV_LIMIT_REG = 0xA2       # U32: PV Power Limit in Watt (keine Begrenzung = 30000)
REMOTE_CONTROL_PUSH_POWER_REG = 0xA4     # S32: Battery Push Power (+Entladung, -Ladung)
REMOTE_CONTROL_DURATION_REG = 0xA6       # U16: Dauer in Sekunden
REMOTE_CONTROL_TIMEOUT_REG = 0xA7        # U16: Timeout in Sekunden

MODE_8_INDIVIDUAL_DURATION = 8
SET_TYPE_SET = 1
PV_LIMIT_NO_CURTAILMENT = 30000
REMOTE_CONTROL_DURATION = 300
REMOTE_CONTROL_TIMEOUT = 300


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
        self.last_mode: Optional[str] = 'Undefined'

    def update(self) -> None:
        power = self.client.read_input_registers(0x0016, ModbusDataType.INT_16, unit=self.__modbus_id)
        soc = self.client.read_input_registers(0x001C, ModbusDataType.UINT_16, unit=self.__modbus_id)
        imported = self.client.read_input_registers(
            0x0021, ModbusDataType.UINT_16, unit=self.__modbus_id) * 100
        exported = self.client.read_input_registers(
            0x001D, ModbusDataType.UINT_16, unit=self.__modbus_id) * 100

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        unit = self.__modbus_id
        max_power = self.component_config.configuration.max_power
        log.debug(f"QCells set_power_limit: power_limit={power_limit}, last_mode={self.last_mode}")

        if power_limit is None:
            log.debug("Keine Batteriesteuerung, Selbstregelung durch Wechselrichter")
            if self.last_mode is not None:
                with self.client:
                    self.client.write_register(
                        REMOTE_CONTROL_MODE_REG, 0, data_type=ModbusDataType.UINT_16, unit=unit)
                self.last_mode = None
        elif power_limit == 0:
            log.debug("Aktive Batteriesteuerung. Batterie wird gestoppt (kein Entladen)")
            if self.last_mode != 'stop':
                self._write_mode8(push_power=0, unit=unit)
                self.last_mode = 'stop'
        elif power_limit > 0:
            charge_power = int(min(power_limit, max_power))
            log.debug(f"Aktive Batteriesteuerung. Batterie wird mit {charge_power} W geladen")
            if self.last_mode != 'charge':
                self.last_mode = 'charge'
            # Solax Mode 8: negativer Push Power Wert = Ladung
            self._write_mode8(push_power=-charge_power, unit=unit)
        elif power_limit < 0:
            discharge_power = int(min(abs(power_limit), max_power))
            log.debug(f"Aktive Batteriesteuerung. Batterie wird mit {discharge_power} W entladen")
            if self.last_mode != 'discharge':
                self.last_mode = 'discharge'
            # Solax Mode 8: positiver Push Power Wert = Entladung
            self._write_mode8(push_power=discharge_power, unit=unit)

    def _write_mode8(self, push_power: int, unit: int) -> None:
        """Schreibt die Mode 8 Remote Control Register (0xA0-0xA7)."""
        with self.client:
            self.client.write_register(
                REMOTE_CONTROL_MODE_REG, MODE_8_INDIVIDUAL_DURATION,
                data_type=ModbusDataType.UINT_16, unit=unit)
            self.client.write_register(
                REMOTE_CONTROL_SET_TYPE_REG, SET_TYPE_SET,
                data_type=ModbusDataType.UINT_16, unit=unit)
            self.client.write_register(
                REMOTE_CONTROL_PV_LIMIT_REG, PV_LIMIT_NO_CURTAILMENT,
                data_type=ModbusDataType.UINT_32, unit=unit)
            self.client.write_register(
                REMOTE_CONTROL_PUSH_POWER_REG, push_power,
                data_type=ModbusDataType.INT_32, unit=unit)
            self.client.write_register(
                REMOTE_CONTROL_DURATION_REG, REMOTE_CONTROL_DURATION,
                data_type=ModbusDataType.UINT_16, unit=unit)
            self.client.write_register(
                REMOTE_CONTROL_TIMEOUT_REG, REMOTE_CONTROL_TIMEOUT,
                data_type=ModbusDataType.UINT_16, unit=unit)

    def power_limit_controllable(self) -> bool:
        return True


component_descriptor = ComponentDescriptor(configuration_factory=QCellsBatSetup)
