#!/usr/bin/env python3
from typing import Tuple, TypedDict, Any

from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_inverter_value_store
from modules.common import req
from modules.devices.kostal.kostal_piko.config import KostalPikoInverterSetup


class KwargsDict(TypedDict):
    ip_address: str


class KostalPikoInverter(AbstractInverter):
    def __init__(self, component_config: KostalPikoInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.ip_address: str = self.kwargs['ip_address']
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> Tuple[float, float]:
        # Die Differenz der Einträge entspricht nicht der Batterieleistung.
        if self.component_config.configuration.bat_configured:
            params = (('dxsEntries', ['33556736', '251658753)']),)
        else:
            params = (('dxsEntries', ['67109120', '251658753)']),)
        resp = req.get_http_session().get('http://'+self.ip_address+'/api/dxs.json', params=params, timeout=3).json()
        power = float(resp["dxsEntries"][0]["value"])
        if power > 5:
            power = power * -1

        exported = float(resp["dxsEntries"][1]["value"]) * 1000

        inverter = InverterState(
            exported=exported,
            power=power
        )
        self.store.set(inverter)
        return inverter


component_descriptor = ComponentDescriptor(configuration_factory=KostalPikoInverterSetup)
