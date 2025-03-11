#!/usr/bin/env python3
from typing import Dict, Union, TypedDict, Any

from modules.common import modbus
from modules.common.abstract_device import AbstractCounter
from modules.common.component_type import ComponentDescriptor
from modules.devices.openwb.openwb_evu_kit.config import EvuKitCounterSetup
from modules.devices.openwb.openwb_flex.counter import EvuKitFlex
from modules.devices.openwb.openwb_flex.config import convert_to_flex_setup


class KwargsDict(TypedDict):
    device_id: int
    client: modbus.ModbusTcpClient_


class EvuKit(EvuKitFlex, AbstractCounter):
    def __init__(self,
                 component_config: Union[Dict, EvuKitCounterSetup],
                 **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__tcp_client: modbus.ModbusTcpClient_ = self.kwargs['client']
        version = self.component_config.configuration.version
        if version == 0:
            id = 5
        elif version == 1:
            id = 2
        elif version == 2:
            id = 115
        elif version == 3:
            id = 105
        else:
            raise ValueError("Version " + str(version) + " unbekannt.")

        super().__init__(convert_to_flex_setup(self.component_config, id),
                         device_id=self.__device_id,
                         client=self.__tcp_client)
        super().initialize()


component_descriptor = ComponentDescriptor(configuration_factory=EvuKitCounterSetup)
