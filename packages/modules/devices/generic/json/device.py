#!/usr/bin/env python3
import logging
from typing import List, Union, Iterable

from helpermodules.cli import run_using_positional_cli_args
from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ConfigurableDevice, ComponentFactoryByType, MultiComponentUpdater
from modules.devices.generic.json import bat, counter, inverter
from modules.devices.generic.json.bat import JsonBat
from modules.devices.generic.json.config import (Json,
                                                 JsonBatConfiguration,
                                                 JsonBatSetup,
                                                 JsonConfiguration,
                                                 JsonCounterConfiguration,
                                                 JsonCounterSetup,
                                                 JsonInverterConfiguration,
                                                 JsonInverterSetup)
from modules.devices.generic.json.counter import JsonCounter
from modules.devices.generic.json.inverter import JsonInverter

log = logging.getLogger(__name__)
JsonComponent = Union[JsonBat, JsonCounter, JsonInverter]


def create_device(device_config: Json):
    def create_bat(component_config: JsonBatSetup) -> JsonBat:
        return JsonBat(device_config.id, component_config)

    def create_counter(component_config: JsonCounterSetup) -> JsonCounter:
        return JsonCounter(device_config.id, component_config)

    def create_inverter(component_config: JsonInverterSetup) -> JsonInverter:
        return JsonInverter(device_config.id, component_config)

    def update_components(components: Iterable[JsonComponent]):
        response = req.get_http_session().get(device_config.configuration.url, timeout=5).json()
        for component in components:
            component.update(response)

    return ConfigurableDevice(
        device_config,
        component_factory=ComponentFactoryByType(bat=create_bat, counter=create_counter, inverter=create_inverter),
        component_updater=MultiComponentUpdater(update_components)
    )


def read_legacy(url: str, component_config: Union[JsonBatSetup, JsonCounterSetup, JsonInverterSetup]) -> None:
    dev = create_device(Json(configuration=JsonConfiguration(url=url)))
    dev.add_component(component_config)
    dev.update()


def read_legacy_bat(ip_address: str, jq_power: str, jq_soc: str):
    config = JsonBatConfiguration(jq_power=jq_power, jq_soc=jq_soc)
    read_legacy(ip_address, bat.component_descriptor.configuration_factory(id=None, configuration=config))


def read_legacy_counter(ip_address: str, jq_power: str, jq_imported: str, jq_exported: str,
                        jq_power_l1: str, jq_power_l2: str, jq_power_l3: str,
                        jq_current_l1: str, jq_current_l2: str, jq_current_l3: str):
    config = JsonCounterConfiguration(jq_power=jq_power,
                                      jq_imported=None if jq_imported == "" else jq_imported,
                                      jq_exported=None if jq_exported == "" else jq_exported,
                                      jq_power_l1=None if jq_power_l1 == "" else jq_power_l1,
                                      jq_power_l2=None if jq_power_l2 == "" else jq_power_l2,
                                      jq_power_l3=None if jq_power_l3 == "" else jq_power_l3,
                                      jq_current_l1=None if jq_current_l1 == "" else jq_current_l1,
                                      jq_current_l2=None if jq_current_l2 == "" else jq_current_l2,
                                      jq_current_l3=None if jq_current_l3 == "" else jq_current_l3
                                      )
    read_legacy(
        ip_address,
        counter.component_descriptor.configuration_factory(id=None, configuration=config))


def read_legacy_inverter(ip_address: str, jq_power: str, jq_exported: str, num: int):
    config = JsonInverterConfiguration(jq_power=jq_power, jq_exported=None if jq_exported == "" else jq_exported)
    read_legacy(ip_address, inverter.component_descriptor.configuration_factory(id=num, configuration=config))


def main(argv: List[str]):
    run_using_positional_cli_args(
        {"bat": read_legacy_bat, "counter": read_legacy_counter, "inverter": read_legacy_inverter}, argv
    )


device_descriptor = DeviceDescriptor(configuration_factory=Json)
