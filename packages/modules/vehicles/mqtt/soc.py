#!/usr/bin/env python3
from typing import List, Union
from modules.common.fault_state import ComponentInfo
import logging
import sys

from dataclass_utils import dataclass_from_dict
from modules.vehicles.mqtt.config import MqttSocSetup
from helpermodules.cli import run_using_positional_cli_args
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_soc import AbstractSoc, SocUpdateData
from modules.common.component_context import SingleComponentUpdateContext

log = logging.getLogger("soc."+__name__)


class Soc(AbstractSoc):
    def __init__(self, device_config: Union[dict, MqttSocSetup], vehicle: int):
        self.config = dataclass_from_dict(MqttSocSetup, device_config)
        self.vehicle = vehicle
        self.component_info = ComponentInfo(self.vehicle, self.config.name, "vehicle")

    def update(self, soc_update_data: SocUpdateData) -> None:
        with SingleComponentUpdateContext(self.component_info):
            log.debug("MQTT-Fahrzeuge müssen nicht ausgelesen werden.")


def mqtt_update(charge_point: int):
    pass


def main(argv: List[str]):
    log.debug('Mqtt SOC main, argv: ' + str(sys.argv[1:]))
    run_using_positional_cli_args(mqtt_update, argv)


device_descriptor = DeviceDescriptor(configuration_factory=MqttSocSetup)
