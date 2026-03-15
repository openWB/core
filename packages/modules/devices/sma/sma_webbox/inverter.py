#!/usr/bin/env python3
from typing import Any, Dict, Union, TypedDict

from modules.common import req
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_inverter_value_store
from modules.devices.sma.sma_webbox.config import SmaWebboxInverterSetup


class KwargsDict(TypedDict):
    ip_address: str


class SmaWebboxInverter(AbstractInverter):
    def __init__(self, component_config: Union[Dict, SmaWebboxInverterSetup], **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.ip_address: str = self.kwargs['ip_address']
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        self.store.set(self.read())

    def read(self) -> InverterState:
        data = {'RPC': '{"version": "1.0","proc": "GetPlantOverview","id": "1","format": "JSON"}'}
        response = req.get_http_session().post(f'http://{self.ip_address}/rpc', data=data, timeout=3).json()

        return InverterState(
            exported=float(response["result"]["overview"][2]["value"]) * 1000,
            power=-int(response["result"]["overview"][0]["value"])
        )


component_descriptor = ComponentDescriptor(configuration_factory=SmaWebboxInverterSetup)
