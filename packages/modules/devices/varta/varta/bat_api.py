#!/usr/bin/env python3
import xml.etree.ElementTree as ET

from typing import TypedDict, Any
from modules.common import req
from modules.common.abstract_device import AbstractBat
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.simcount import SimCounter
from modules.common.store import get_component_value_store
from modules.devices.varta.varta.config import VartaBatApiSetup


class KwargsDict(TypedDict):
    device_id: int
    ip_address: str


class VartaBatApi(AbstractBat):
    def __init__(self, component_config: VartaBatApiSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.__device_id: int = self.kwargs['device_id']
        self.ip_address: str = self.kwargs['ip_address']
        self.sim_counter = SimCounter(self.__device_id, self.component_config.id, self.component_config.type)
        self.store = get_component_value_store(self.component_config.type, self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        def get_xml_text(attribute_value: str) -> float:
            value = None
            for element in root[0].iter("var"):
                if element.attrib["name"] == attribute_value:
                    value = element.attrib["value"]
            try:
                return float(value)
            except ValueError:
                # Wenn Speicher aus bzw. im Standby (keine Antwort), ersetze leeren Wert durch eine 0.
                return 0

        response = req.get_http_session().get('http://'+self.ip_address+'/cgi/ems_data.xml',
                                              timeout=5)
        response.encoding = 'utf-8'
        response = response.text.replace("\n", "")
        root = ET.fromstring(response)

        power = get_xml_text("P")
        soc = get_xml_text("SOC") / 10

        imported, exported = self.sim_counter.sim_count(power)

        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=VartaBatApiSetup)
