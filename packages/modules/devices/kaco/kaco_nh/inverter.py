#!/usr/bin/env python3
from typing import Dict, TypedDict, Any

from modules.common import req
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_inverter_value_store
from modules.devices.kaco.kaco_nh.config import KacoNHInverterSetup
from modules.devices.kaco.kaco_nh.config import KacoNHConfiguration


class KwargsDict(TypedDict):
    device_config: KacoNHConfiguration


class KacoNHInverter(AbstractInverter):
    def __init__(self, component_config: KacoNHInverterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.device_config: KacoNHConfiguration = self.kwargs['device_config']
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self, response: Dict) -> None:
        response = req.get_http_session().get(
            'http://' + self.device_config.ip_address + ':' + str(self.device_config.port) + '/getdevdata.cgi?device=' +
            str(self.component_config.configuration.id) + '&sn=' + self.device_config.serial_number,
            timeout=5).json()

        power = float(response["pac"]) * -1
        exported = float(response["eto"]) * 100

        self.store.set(InverterState(
            power=power,
            exported=exported
        ))


component_descriptor = ComponentDescriptor(configuration_factory=KacoNHInverterSetup)
