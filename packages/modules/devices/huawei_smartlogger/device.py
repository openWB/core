#!/usr/bin/env python3
import logging
from typing import Optional, Union, List, Dict
from dataclass_utils import dataclass_from_dict
from helpermodules.cli import run_using_positional_cli_args
from modules.common.abstract_device import AbstractDevice, DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common import modbus
from modules.devices.huawei_smartlogger import counter
from modules.devices.huawei_smartlogger import inverter
from modules.devices.huawei_smartlogger import bat
from modules.devices.huawei_smartlogger.config import Huawei_Smartlogger, Huawei_SmartloggerBatSetup
from modules.devices.huawei_smartlogger.config import Huawei_SmartloggerCounterSetup, Huawei_SmartloggerInverterSetup


log = logging.getLogger(__name__)


huawei_smartlogger_component_classes = Union[bat.Huawei_SmartloggerBat, counter.Huawei_SmartloggerCounter, inverter.Huawei_SmartloggerInverter]


class Device(AbstractDevice):
    COMPONENT_TYPE_TO_CLASS = {
        "bat": bat.Huawei_SmartloggerBat,
        "counter": counter.Huawei_SmartloggerCounter,
        "inverter": inverter.Huawei_SmartloggerInverter
    }

    def __init__(self, device_config: Union[Dict, Huawei_Smartlogger]) -> None:
        self.components = {}  # type: Dict[str, huawei_smartlogger_component_classes]
        try:
            self.device_config = dataclass_from_dict(Huawei_Smartlogger, device_config)
            ip_address = self.device_config.configuration.ip_address
            self.port = 502
            self.client = modbus.ModbusTcpClient_(ip_address, 502)
            self.client.delegate.connect()
        except Exception:
            log.exception("Fehler im Modul "+self.device_config.name)

    def add_component(self, component_config: Union[Dict,
                                                    Huawei_SmartloggerBatSetup,
                                                    Huawei_SmartloggerCounterSetup,
                                                    Huawei_SmartloggerInverterSetup]) -> None:
        if isinstance(component_config, Dict):
            component_type = component_config["type"]
        else:
            component_type = component_config.type
        component_config = dataclass_from_dict(COMPONENT_TYPE_TO_MODULE[
            component_type].component_descriptor.configuration_factory, component_config)
        if component_type in self.COMPONENT_TYPE_TO_CLASS:
            self.components["component"+str(component_config.id)] = (
                self.COMPONENT_TYPE_TO_CLASS[component_type](self.device_config.id, component_config, self.client))
        else:
            raise Exception(
                "illegal component type " + component_type + ". Allowed values: " +
                ','.join(self.COMPONENT_TYPE_TO_CLASS.keys())
            )

    def update(self) -> None:
        log.debug("Start device reading " + str(self.components))
        if self.components:
            for component in self.components:
                # Auch wenn bei einer Komponente ein Fehler auftritt, sollen alle anderen noch ausgelesen werden.
                with SingleComponentUpdateContext(self.components[component].component_info):
                    self.components[component].update()
        else:
            log.warning(
                self.device_config.name +
                ": Es konnten keine Werte gelesen werden, da noch keine Komponenten konfiguriert wurden."
            )


COMPONENT_TYPE_TO_MODULE = {
    "bat": bat,
    "counter": counter,
    "inverter": inverter
}


def read_legacy(component_type: str,
                ip_address: str,
                modbus_id: Optional[int] = 1,
                num: Optional[int] = None) -> None:

    device_config = Huawei_Smartlogger()
    device_config.configuration.ip_address = ip_address
    dev = Device(device_config)

    if component_type in COMPONENT_TYPE_TO_MODULE:
        component_config = COMPONENT_TYPE_TO_MODULE[component_type].component_descriptor.configuration_factory()
    else:
        raise Exception("illegal component type " + component_type + ". Allowed values: " +
                        ','.join(COMPONENT_TYPE_TO_MODULE.keys())
        )
    component_config.id = num
    component_config.configuration.modbus_id = modbus_id
    dev.add_component(component_config)

    log.debug('Huawei Smartlogger IP-Adresse: ' + ip_address)
    log.debug('Huawei Device Modbus-ID: ' + str(modbus_id))
    dev.update()


def main(argv: List[str]):
    run_using_positional_cli_args(read_legacy, argv)


device_descriptor = DeviceDescriptor(configuration_factory=Huawei_Smartlogger)
