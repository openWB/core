#!/usr/bin/env python3
from typing import List, Union
from modules.common.fault_state import ComponentInfo
import logging
import sys

from dataclass_utils import dataclass_from_dict
from modules.mqtt.config import MqttSocSetup
from helpermodules.cli import run_using_positional_cli_args
from modules.common import store
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_soc import AbstractSoc

log = logging.getLogger("soc."+__name__)


class Soc(AbstractSoc):
    def __init__(self, device_config: Union[dict, MqttSocSetup], vehicle: int):
        self.config = dataclass_from_dict(MqttSocSetup, device_config)
        self.vehicle = vehicle
        self.store = store.get_car_value_store(self.vehicle)
        self.component_info = ComponentInfo(self.vehicle, self.config.name, "vehicle")

    def update(self, charge_state: bool = False) -> None:
        pass


def mqtt_update(charge_point: int):
    pass


def main(argv: List[str]):
    log.debug('Mqtt SOC main, argv: ' + sys.argv[1:])
    run_using_positional_cli_args(mqtt_update, argv)


device_descriptor = DeviceDescriptor(configuration_factory=MqttSocSetup)
