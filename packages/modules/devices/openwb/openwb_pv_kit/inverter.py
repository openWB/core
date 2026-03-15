#!/usr/bin/env python3
from typing import Union, TypedDict, Any

from modules.common import modbus
from modules.common.abstract_device import AbstractInverter
from modules.common.component_type import ComponentDescriptor
from modules.devices.openwb.openwb_evu_kit.config import EvuKitInverterSetup
from modules.devices.openwb.openwb_flex.config import convert_to_flex_setup
from modules.devices.openwb.openwb_flex.inverter import PvKitFlex
from modules.devices.openwb.openwb_pv_kit.config import PvKitInverterSetup


class KwargsDict(TypedDict):
    device_id: int
    client: modbus.ModbusTcpClient_


class PvKit(PvKitFlex, AbstractInverter):
    def __init__(self,
                 component_config: Union[EvuKitInverterSetup, PvKitInverterSetup],
                 **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.__tcp_client: modbus.ModbusTcpClient_ = self.kwargs['client']
        version = self.component_config.configuration.version
        if version == 0 or version == 1:
            id = 8
        elif version == 2:
            id = 116
        else:
            raise ValueError("Version "+str(version) + " unbekannt.")

        super().__init__(convert_to_flex_setup(self.component_config, id),
                         device_id=self.__device_id,
                         client=self.__tcp_client)
        super().initialize()


component_descriptor = ComponentDescriptor(configuration_factory=PvKitInverterSetup)
