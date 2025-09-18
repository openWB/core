
import logging
from typing import Iterable, Union, List

from modules.common.modbus import ModbusDataType
from modules.devices.solaredge.solaredge.config import (SolaredgeBatSetup, SolaredgeCounterSetup,
                                                        SolaredgeExternalInverterSetup, SolaredgeInverterSetup)
log = logging.getLogger(__name__)


synergy_unit_identifier = 160


class SolaredgeMeterRegisters:
    def __init__(self, internal_meter_id: int = 1, synergy_units: int = 1):
        # 40206: Total Real Power (sum of active phases)
        # 40207/40208/40209: Real Power by phase
        # 40210: AC Real Power Scale Factor
        self.power = 40206
        self.powers = 40207
        self.powers_scale = 40210
        # 40191/40192/40193: AC Current by phase
        # 40194: AC Current Scale Factor
        self.currents = 40191
        self.currents_scale = 40194
        # 40196/40197/40198: Voltage per phase
        # 40203: AC Voltage Scale Factor
        self.voltages = 40196
        self.voltages_scale = 40203
        # 40204: AC Frequency
        # 40205: AC Frequency Scale Factor
        self.frequency = 40204
        self.frequency_scale = 40205
        # 40222/40223/40224: Power factor by phase (unit=%)
        # 40225: AC Power Factor Scale Factor
        self.power_factors = 40222
        self.power_factors_scale = 40225
        # 40226: Total Exported Real Energy
        # 40228/40230/40232: Total Exported Real Energy Phase (not used)
        # 40234: Total Imported Real Energy
        # 40236/40238/40240: Total Imported Real Energy Phase (not used)
        # 40242: Real Energy Scale Factor
        self.exported = 40226
        self.imported = 40234
        self.imp_exp_scale = 40242
        # 40155: C_Option Export + Import, Production, consumption,
        self.option = 40155
        self._update_offset_meter_id(internal_meter_id)
        self._update_offset_synergy_units(synergy_units)

    def _update_offset_meter_id(self, meter_id: int) -> None:
        OFFSET = [0, 174, 348]
        self._add_offset(OFFSET[meter_id-1])

    def _update_offset_synergy_units(self, synergy_units: int) -> None:
        """https://www.solaredge.com/sites/default/files/sunspec-implementation-technical-note.pdf:
        For 2-unit three phase inverters with Synergy technology, add 50 to the default addresses.
        For 3-unit three phase inverters with Synergy technology, add 70 to the default addresses.
        """
        OFFSET = [0, 50, 70]
        try:
            self._add_offset(OFFSET[synergy_units-1])
        except IndexError:
            log.debug("Undocumented synergy units value "+str(synergy_units)+". Use synergy_units 1.")
            self._add_offset(OFFSET[0])

    def _add_offset(self, offset: int) -> None:
        for name, value in self.__dict__.items():
            setattr(self, name, value+offset)


def _set_registers(components: Iterable,
                   synergy_units: int,
                   modbus_id: int) -> None:
    meters: List = [None]*3
    for component in components:
        if (isinstance(component.component_config, (SolaredgeCounterSetup, SolaredgeExternalInverterSetup)) and
                component.component_config.configuration.modbus_id == modbus_id):
            # Registerverschibung nur für Komponenten mit gleicher Modbus-ID, da diese am gleichen Haupt-WR hängen
            # und die gleichen Synergy-Units haben.
            meters[component.component_config.configuration.meter_id-1] = component

    # https://www.solaredge.com/sites/default/files/sunspec-implementation-technical-note.pdf:
    # Only enabled meters are readable, i.e. if meter 1 and 3 are enabled, they are readable as 1st meter and 2nd
    # meter (and the 3rd meter isn't readable).
    for meter_id, meter in enumerate(filter(None, meters), start=1):
        log.debug(
            "%s: internal meter id: %d, synergy units: %s", meter.component_config.name, meter_id, synergy_units
        )
        meter.registers = SolaredgeMeterRegisters(meter_id, synergy_units)


def _get_synergy_units(component_config: Union[SolaredgeBatSetup,
                                               SolaredgeCounterSetup,
                                               SolaredgeInverterSetup,
                                               SolaredgeExternalInverterSetup],
                       client) -> int:
    if client.read_holding_registers(40121, ModbusDataType.UINT_16,
                                     unit=component_config.configuration.modbus_id
                                     ) == synergy_unit_identifier:
        # Snyergy-Units vom Haupt-WR des angeschlossenen Meters ermitteln. Es kann mehrere Haupt-WR mit
        # unterschiedlichen Modbus-IDs im Verbund geben.
        log.debug("Synergy Units supported")
        synergy_units = int(client.read_holding_registers(
            40129, ModbusDataType.UINT_16,
            unit=component_config.configuration.modbus_id)) or 1
        log.debug(
            f"Synergy Units detected for Modbus ID {component_config.configuration.modbus_id}: {synergy_units}")
    else:
        synergy_units = 1
    return synergy_units


def set_component_registers(component_config: Union[SolaredgeBatSetup,
                                                    SolaredgeCounterSetup,
                                                    SolaredgeInverterSetup,
                                                    SolaredgeExternalInverterSetup],
                            client,
                            components: Iterable) -> None:
    synergy_units = _get_synergy_units(component_config, client)
    _set_registers(components, synergy_units, component_config.configuration.modbus_id)
