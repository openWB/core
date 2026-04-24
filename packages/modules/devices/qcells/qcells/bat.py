#!/usr/bin/env python3
import logging
from typing import Any, Optional, TypedDict

from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadBuilder

from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor, ComponentType
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.modbus import ModbusDataType, ModbusTcpClient_
from modules.common.store import get_bat_value_store
from modules.common.utils.peak_filter import PeakFilter
from modules.devices.qcells.qcells.config import QCellsBatSetup

log = logging.getLogger(__name__)

# Solax/QCells Remote Control Registers (Holding Registers)
REMOTE_CONTROL_MODE_REG = 0x7C
REMOTE_CONTROL_SET_TYPE_REG = 0x7D
REMOTE_CONTROL_ACTIVE_POWER_REG = 0x7E
REMOTE_CONTROL_REACTIVE_POWER_REG = 0x80
REMOTE_CONTROL_DURATION_REG = 0x82
REMOTE_CONTROL_TARGET_SOC_REG = 0x83
REMOTE_CONTROL_TARGET_ENERGY_REG = 0x84
REMOTE_CONTROL_TARGET_POWER_REG = 0x86
REMOTE_CONTROL_TIMEOUT_REG = 0x88
REMOTE_CONTROL_PUSH_POWER_MODE4_REG = 0x89

MODE_DISABLED = 0
MODE_4_PUSH_POWER = 4
SET_TYPE_SET = 1
MODE_4_TIMEOUT_DISABLED = 0
MODE4_BLOCK_REG_COUNT = 15


class KwargsDict(TypedDict):
    modbus_id: int
    client: ModbusTcpClient_


class QCellsBat(AbstractBat):
    def __init__(self, component_config: QCellsBatSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__modbus_id: int = self.kwargs["modbus_id"]
        self.client: ModbusTcpClient_ = self.kwargs["client"]
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.BAT, self.component_config.id, self.fault_state)
        self.last_mode: Optional[str] = "Undefined"

    def update(self) -> None:
        power = self.client.read_input_registers(0x0016, ModbusDataType.INT_16, unit=self.__modbus_id)
        soc = self.client.read_input_registers(0x001C, ModbusDataType.UINT_16, unit=self.__modbus_id)
        imported = self.client.read_input_registers(0x0021, ModbusDataType.UINT_16, unit=self.__modbus_id) * 100
        exported = self.client.read_input_registers(0x001D, ModbusDataType.UINT_16, unit=self.__modbus_id) * 100

        imported, exported = self.peak_filter.check_values(power, imported, exported)
        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported,
        )
        self.store.set(bat_state)

    def set_power_limit(self, power_limit: Optional[int]) -> None:
        unit = self.__modbus_id
        log.debug(f"QCells set_power_limit: power_limit={power_limit}, last_mode={self.last_mode}")

        if power_limit is None:
            log.debug("Keine Batteriesteuerung, Selbstregelung durch Wechselrichter")
            if self.last_mode is not None:
                with self.client:
                    self.client.write_register(
                        REMOTE_CONTROL_MODE_REG,
                        MODE_DISABLED,
                        data_type=ModbusDataType.UINT_16,
                        unit=unit,
                    )
                self.last_mode = None
            return

        if power_limit < 0:
            self.last_mode = "discharge"
        elif power_limit > 0:
            self.last_mode = "charge"
        else:
            self.last_mode = "stop"

        push_power = self._get_mode4_push_power(int(power_limit))
        self._write_mode4(push_power, unit)

    def _get_mode4_push_power(self, power_limit: int) -> int:
        # openWB power_limit semantics:
        # <0 discharge, 0 stop, >0 charge
        # Mode 4 push_power semantics:
        # >0 discharge, 0 stop, <0 charge
        push_power = int(power_limit * -1)
        log.debug(f"QCells Mode4 target: power_limit={power_limit}W -> push_power={push_power}W")
        return push_power

    def _write_mode4(self, push_power: int, unit: int) -> None:
        log.debug(
            (
                f"QCells Mode4 write: mode={MODE_4_PUSH_POWER}, set_type={SET_TYPE_SET}, "
                f"timeout={MODE_4_TIMEOUT_DISABLED}s, push_power={push_power}W"
            )
        )
        builder = BinaryPayloadBuilder(byteorder=Endian.Big, wordorder=Endian.Little)
        builder.add_16bit_uint(MODE_4_PUSH_POWER)
        builder.add_16bit_uint(SET_TYPE_SET)
        builder.add_32bit_int(0)
        builder.add_32bit_int(0)
        builder.add_16bit_uint(0)
        builder.add_16bit_uint(0)
        builder.add_32bit_uint(0)
        builder.add_32bit_int(0)
        builder.add_16bit_uint(MODE_4_TIMEOUT_DISABLED)
        builder.add_32bit_int(push_power)
        payload = builder.to_registers()
        if len(payload) != MODE4_BLOCK_REG_COUNT:
            raise RuntimeError(
                f"Unexpected mode4 payload size {len(payload)}, expected {MODE4_BLOCK_REG_COUNT}"
            )

        with self.client:
            # data_type=None with list payload writes a contiguous FC16 block.
            self.client.write_register(REMOTE_CONTROL_MODE_REG, payload, unit=unit)

    def power_limit_controllable(self) -> bool:
        return True


component_descriptor = ComponentDescriptor(configuration_factory=QCellsBatSetup)
