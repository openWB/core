#!/usr/bin/env python3
import logging
from typing import TypedDict, Any

from requests import Session

from modules.common import req
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_inverter_value_store
from modules.devices.fronius.fronius.config import FroniusConfiguration, MeterLocation
from modules.devices.fronius.fronius.config import FroniusProductionCounterSetup

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    device_id: int
    device_config: FroniusConfiguration


class FroniusProductionCounter(AbstractCounter):
    def __init__(self, component_config: FroniusProductionCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.device_config: FroniusConfiguration = self.kwargs['device_config']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, prefix="pv")
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        session = req.get_http_session()
        variant = self.component_config.configuration.variant
        if variant == 0 or variant == 1:
            inverter_state = self.__update_variant_0_1(session)
        elif variant == 2:
            inverter_state = self.__update_variant_2(session)
        else:
            raise ValueError("Unbekannte Variante: "+str(variant))
        self.store.set(inverter_state)

    def __update_variant_0_1(self, session: Session) -> InverterState:
        variant = self.component_config.configuration.variant
        meter_id = self.component_config.configuration.meter_id
        if variant == 0:
            params = (
                ('Scope', 'Device'),
                ('DeviceId', meter_id),
            )
        elif variant == 1:
            params = (
                ('Scope', 'Device'),
                ('DeviceId', meter_id),
                ('DataCollection', 'MeterRealtimeData'),
            )
        else:
            raise ValueError("Unbekannte Generation: "+str(variant))
        response = session.get(
            'http://' + self.device_config.ip_address + '/solar_api/v1/GetMeterRealtimeData.cgi',
            params=params,
            timeout=5)
        response_json_id = response.json()["Body"]["Data"]

        meter_location = MeterLocation.get(response_json_id["Meter_Location_Current"])
        log.debug("Einbauort: "+str(meter_location))

        powers = [response_json_id["PowerReal_P_Phase_"+str(num)] for num in range(1, 4)]
        if meter_location != MeterLocation.external:
            raise ValueError("Fehler: Dieser Zähler ist kein Erzeugerzähler.")
        else:
            power = response_json_id["PowerReal_P_Sum"] * -1
            voltages = [response_json_id["Voltage_AC_Phase_"+str(num)] for num in range(1, 4)]
            currents = [powers[i] / voltages[i] for i in range(0, 3)]
            _, exported = self.sim_counter.sim_count(power)
        return InverterState(
            currents=currents,
            power=power,
            exported=exported
        )

    def __update_variant_2(self, session: Session) -> InverterState:
        meter_id = str(self.component_config.configuration.meter_id)
        response = session.get(
            'http://' + self.device_config.ip_address + '/solar_api/v1/GetMeterRealtimeData.cgi',
            params=(('Scope', 'System'),),
            timeout=5)
        response_json_id = dict(response.json()["Body"]["Data"]).get(meter_id)

        meter_location = MeterLocation.get(response_json_id["SMARTMETER_VALUE_LOCATION_U16"])
        log.debug("Einbauort: "+str(meter_location))

        powers = [response_json_id["SMARTMETER_POWERACTIVE_MEAN_0"+str(num)+"_F64"] for num in range(1, 4)]
        if meter_location != MeterLocation.external:
            raise ValueError("Fehler: Dieser Zähler ist kein Erzeugerzähler.")
        else:
            power = response_json_id["SMARTMETER_POWERACTIVE_MEAN_SUM_F64"]
            voltages = [response_json_id["SMARTMETER_VOLTAGE_0"+str(num)+"_F64"] for num in range(1, 4)]
            currents = [powers[i] / voltages[i] for i in range(0, 3)]
            _, exported = self.sim_counter.sim_count(power)
        return InverterState(
            currents=currents,
            power=power,
            exported=exported
        )


component_descriptor = ComponentDescriptor(configuration_factory=FroniusProductionCounter)
