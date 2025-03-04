#!/usr/bin/env python3
import logging
from typing import Any, TypedDict
import xml.etree.ElementTree as ET

from modules.common import req
from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_counter_value_store
from modules.devices.smartfox.smartfox.config import SmartfoxCounterSetup

log = logging.getLogger(__name__)


class KwargsDict(TypedDict):
    ip_address: str


class SmartfoxCounter(AbstractCounter):
    def __init__(self, component_config: SmartfoxCounterSetup, **kwargs: Any) -> None:
        self.component_config = component_config
        self.kwargs: KwargsDict = kwargs

    def initialize(self) -> None:
        self.ip_address: int = self.kwargs['ip_address']
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    def update(self) -> None:
        def get_xml_text(attribute_value: str) -> str:
            value = None
            for element in self.root.iter("value"):
                if element.get("id") == attribute_value:
                    value = element.text
            return value

        headers = {
            'Accept': '*/*',
            'Accept-Encoding': 'gzip, deflate',
            'Host': self.ip_address,
            'Connection': 'keep-alive)',
        }

        response = req.get_http_session().get('http://'+self.ip_address+'/values.xml',
                                              headers=headers,
                                              timeout=5)
        response.encoding = 'utf-8'
        response = response.text.replace("\n", "")
        # Version ermitteln
        self.root = ET.fromstring(response)

        # Leistungsfaktor ist nach dem Firmwareupgrade auf EM2 00.01.03.06 (04-2021)
        # nicht mehr in der values.xml daher fix auf 1

        self.store.set(CounterState(
            imported=float((get_xml_text("energyValue"))[:-4]) * 1000,
            exported=float((get_xml_text("eToGridValue"))[:-4]) * 1000,
            power=float((get_xml_text("detailsPowerValue"))[:-2]),
            powers=[float(get_xml_text(key)[:-2]) for key in ["powerL1Value", "powerL2Value", "powerL3Value"]],
            voltages=[float(get_xml_text(key)[:-2]) for key in ["voltageL1Value", "voltageL2Value", "voltageL3Value"]],
            currents=[float(get_xml_text(key)[:-2]) for key in ["ampereL1Value", "ampereL2Value", "ampereL3Value"]]

        ))


component_descriptor = ComponentDescriptor(configuration_factory=SmartfoxCounterSetup)
