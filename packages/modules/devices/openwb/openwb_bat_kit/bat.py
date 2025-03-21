#!/usr/bin/env python3
from typing import Union

from modules.common import modbus
from modules.common.abstract_device import AbstractBat
from modules.common.component_type import ComponentDescriptor
from modules.devices.openwb.openwb_bat_kit.config import BatKitBatSetup
from modules.devices.openwb.openwb_evu_kit.config import EvuKitBatSetup
from modules.devices.openwb.openwb_flex.bat import BatKitFlex
from modules.devices.openwb.openwb_flex.config import convert_to_flex_setup


class BatKit(BatKitFlex, AbstractBat):
    def __init__(self,
                 device_id: int,
                 component_config: Union[BatKitBatSetup, EvuKitBatSetup],
                 tcp_client: modbus.ModbusTcpClient_) -> None:
        self.component_config = component_config
        version = self.component_config.configuration.version
        if version == 0:
            id = 1
        elif version == 1:
            id = 9
        elif version == 2:
            id = 117
        else:
            raise ValueError("Version " + str(version) + " unbekannt.")

        super().__init__(device_id, convert_to_flex_setup(self.component_config, id), tcp_client)


component_descriptor = ComponentDescriptor(configuration_factory=BatKitBatSetup)
