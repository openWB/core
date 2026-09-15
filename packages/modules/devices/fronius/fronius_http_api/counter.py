#!/usr/bin/env python3
import logging
from typing import Dict, Optional, TypedDict, Any

from modules.common import req
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.fronius.fronius_http_api import meter_reader
from modules.devices.fronius.fronius_http_api.config import FroniusConfiguration, MeterLocation, COUNTER_VARIANT_S0
from modules.devices.fronius.fronius_http_api.config import FroniusCounterSetup
from modules.common.utils.peak_filter import PeakFilter
from modules.common.component_type import ComponentType

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    device_config: FroniusConfiguration


class FroniusCounter(AbstractCounter):
    def __init__(self, component_config: FroniusCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.device_config: FroniusConfiguration = self.kwargs['device_config']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.peak_filter = PeakFilter(ComponentType.COUNTER, self.component_config.id, self.fault_state)
        self.cache_key = f"{self.component_config.type}_{self.component_config.id}"

    def update(self, powerflow_response: Dict, meter_system_response: Optional[Dict] = None) -> None:
        config = self.component_config.configuration

        if config.variant == COUNTER_VARIANT_S0:
            # Im Wechselrichter integrierter S0-Zähler: keine eigene SmartMeter-Hardware, sondern der
            # Netz-Wert aus der ohnehin abgerufenen PowerFlow-Antwort.
            if isinstance(powerflow_response, Exception):
                raise powerflow_response
            power = float(powerflow_response["Body"]["Data"]["Site"]["P_Grid"]) or 0
            self.peak_filter.check_values(power)
            imported, exported = self.sim_counter.sim_count(power)
            self.store.set(CounterState(imported=imported, exported=exported, power=power))
            return

        meter = meter_reader.read_meter(
            req.get_http_session(), self.device_config.ip_address, config.meter_id, config.variant,
            self.cache_key, meter_system_response)

        if meter.location == MeterLocation.load:
            power, power_inverter = meter_reader.get_flow_power(powerflow_response)
            # wenn SmartMeter im Verbrauchszweig sitzt sind folgende Annahmen getroffen:
            # PV Leistung wird gleichmäßig auf alle Phasen verteilt
            # Spannungen und Leistungsfaktoren sind am Verbrauchszweig == Einspeisepunkt
            # Hier gehen wir mal davon aus, dass der Wechselrichter seine PV-Leistung gleichmäßig
            # auf alle Phasen aufteilt.
            powers = [-1 * p - power_inverter / 3 for p in meter.powers]
        else:
            powers = meter.powers
            power = meter.power_sum
            # for all meter locations except "grid", negative power is consumption!
            if meter.location in (MeterLocation.external, MeterLocation.subload):
                power *= -1

        currents = [powers[i] / meter.voltages[i] for i in range(0, 3)]

        counter_state = CounterState(
            voltages=meter.voltages,
            currents=currents,
            powers=powers,
            power=power,
            frequency=meter.frequency,
            power_factors=meter.power_factors
        )
        self.peak_filter.check_values(counter_state.power)
        counter_state.imported, counter_state.exported = self.sim_counter.sim_count(counter_state.power)
        self.store.set(counter_state)


component_descriptor = ComponentDescriptor(configuration_factory=FroniusCounterSetup)
