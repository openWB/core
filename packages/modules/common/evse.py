#!/usr/bin/env python3
import logging
from enum import IntEnum
import time
from typing import Optional, Tuple
from helpermodules.logger import ModifyLoglevelContext

from modules.common import modbus
from modules.common.component_state import EvseState
from modules.common.modbus import ModbusDataType

log = logging.getLogger(__name__)


class EvseStatusCode(IntEnum):
    READY = (1, False, False)
    EV_PRESENT = (2, True, False)
    CHARGING = (3, True, True)
    CHARGING_WITH_VENTILATION = (4, True, True)
    FAILURE = (5, None, None)

    def __new__(cls, num: int, plugged: Optional[bool], charge_enabled: Optional[bool]):
        member = int.__new__(cls, num)
        member._value_ = num
        member.plugged = plugged
        member.charge_enabled = charge_enabled
        return member


class Evse:
    PRECISE_CURRENT_BIT = 1 << 7

    def __init__(self, modbus_id: int, client: modbus.ModbusSerialClient_) -> None:
        self.client = client
        self.id = modbus_id
        with client:
            time.sleep(0.1)
            self.version = self.client.read_holding_registers(1005, ModbusDataType.UINT_16, device_id=self.id)
            time.sleep(0.1)
            self.max_current = self.client.read_holding_registers(2007, ModbusDataType.UINT_16, device_id=self.id)
            with ModifyLoglevelContext(log, logging.DEBUG):
                log.debug(f"Firmware-Version der EVSE: {self.version}")
            if self.version < 17:
                self._precise_current = False
            else:
                if self.is_precise_current_active() is False:
                    self.activate_precise_current()
                self._precise_current = self.is_precise_current_active()

    def get_plug_charge_state(self) -> Tuple[bool, bool, float]:
        time.sleep(0.1)
        raw_set_current, _, state_number = self.client.read_holding_registers(
            1000, [ModbusDataType.UINT_16]*3, device_id=self.id)
        # remove leading zeros
        self.evse_current = int(raw_set_current)
        log.debug("Gesetzte Stromstärke EVSE: "+str(self.evse_current) +
                  ", Status: "+str(state_number)+", Modbus-ID: "+str(self.id))
        state = EvseStatusCode(state_number)
        if state == EvseStatusCode.FAILURE:
            raise ValueError("Unbekannter Zustand der EVSE: State " +
                             str(state)+", Soll-Stromstärke: "+str(self.evse_current))
        plugged = state.plugged
        charging = self.evse_current > 0 if state.charge_enabled else False
        if self.evse_current > 32:
            self.evse_current = self.evse_current / 100
        return plugged, charging, self.evse_current

    def get_firmware_version(self) -> int:
        return self.version

    def get_evse_state(self) -> EvseState:
        plugged, charging, set_current = self.get_plug_charge_state()
        state = EvseState(plug_state=plugged,
                          charge_state=charging,
                          set_current=set_current,
                          max_current=self.max_current)
        return state

    def is_precise_current_active(self) -> bool:
        time.sleep(0.1)
        value = self.client.read_holding_registers(2005, ModbusDataType.UINT_16, device_id=self.id)
        with ModifyLoglevelContext(log, logging.DEBUG):
            if value & self.PRECISE_CURRENT_BIT:
                log.debug("Angabe der Ströme in 0,01A-Schritten ist aktiviert.")
                return True
            else:
                log.debug("Angabe der Ströme in 0,01A-Schritten ist nicht aktiviert.")
                return False

    def activate_precise_current(self) -> None:
        time.sleep(0.1)
        value = self.client.read_holding_registers(2005, ModbusDataType.UINT_16, device_id=self.id)
        if value & self.PRECISE_CURRENT_BIT:
            return
        else:
            with ModifyLoglevelContext(log, logging.DEBUG):
                log.debug("Bit zur Angabe der Ströme in 0,1A-Schritten wird gesetzt.")
            self.client.write_registers(2005, value ^ self.PRECISE_CURRENT_BIT, device_id=self.id)
            # Zeit zum Verarbeiten geben
            time.sleep(1)

    def deactivate_precise_current(self) -> None:
        time.sleep(0.1)
        value = self.client.read_holding_registers(2005, ModbusDataType.UINT_16, device_id=self.id)
        if value & self.PRECISE_CURRENT_BIT:
            with ModifyLoglevelContext(log, logging.DEBUG):
                log.debug("Bit zur Angabe der Ströme in 0,1A-Schritten wird zurueckgesetzt.")
            self.client.write_registers(2005, value ^ self.PRECISE_CURRENT_BIT, device_id=self.id)
        else:
            return

    def set_current(self, current: int) -> None:
        time.sleep(0.1)
        formatted_current = round(current*100) if self._precise_current else round(current)
        if self.evse_current != formatted_current:
            self.client.write_registers(1000, formatted_current, device_id=self.id)
