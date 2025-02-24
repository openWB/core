#!/usr/bin/env python3
from typing import Union, TypedDict, Any

from modules.common import modbus
from modules.common.abstract_device import AbstractBat
from modules.common.component_type import ComponentDescriptor
from modules.devices.openwb.openwb_bat_kit.config import BatKitBatSetup
from modules.devices.openwb.openwb_evu_kit.config import EvuKitBatSetup
from modules.devices.openwb.openwb_flex.bat import BatKitFlex
from modules.devices.openwb.openwb_flex.config import convert_to_flex_setup


class KwargsDict(TypedDict):
    device_id: int
    client: modbus.ModbusTcpClient_


class BatKit(BatKitFlex, AbstractBat):
    def __init__(self, component_config: Union[BatKitBatSetup, EvuKitBatSetup], **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.client: modbus.ModbusTcpClient_ = self.kwargs['client']
        version = self.component_config.configuration.version
        if version == 0:
            id = 1
        elif version == 1:
            id = 9
        elif version == 2:
            id = 117
        else:
            raise ValueError("Version " + str(version) + " unbekannt.")

        super().__init__(convert_to_flex_setup(self.component_config, id),
                         device_id=self.__device_id,
                         client=self.client)
        super().initialize()


component_descriptor = ComponentDescriptor(configuration_factory=BatKitBatSetup)
