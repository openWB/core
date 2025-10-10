#!/usr/bin/env python3
import json
import logging
from typing import Dict, Iterable, Union
from requests import HTTPError, Session

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.devices.lg.lg.bat import LgBat
from modules.devices.lg.lg.config import LG, LgBatSetup, LgCounterSetup, LgInverterSetup
from modules.devices.lg.lg.counter import LgCounter
from modules.devices.lg.lg.inverter import LgInverter

log = logging.getLogger(__name__)


def _update_session_key(session: Session, ip_address: str, password: str) -> str:
    try:
        headers = {'Content-Type': 'application/json', }
        data = json.dumps({"password": password})
        response = session.put(f"https://{ip_address}/v1/login", headers=headers,
                               data=data, verify=False, timeout=5).json()
        return response["auth_key"]
    except (HTTPError, KeyError) as e:
        e.args += ("login failed! check password!", )
        raise e


def _request_data(session: Session, session_key: str, ip_address: str) -> Dict:
    headers = {'Content-Type': 'application/json', }
    data = json.dumps({"auth_key": session_key})
    return session.post(f"https://{ip_address}/v1/user/essinfo/home",
                        headers=headers,
                        data=data,
                        verify=False,
                        timeout=5).json()


def create_device(device_config: LG):
    def create_bat_component(component_config: LgBatSetup):
        return LgBat(component_config, device_id=device_config.id)

    def create_counter_component(component_config: LgCounterSetup):
        return LgCounter(component_config, device_id=device_config.id)

    def create_inverter_component(component_config: LgInverterSetup):
        return LgInverter(component_config, device_id=device_config.id)

    def update_components(components: Iterable[Union[LgBat, LgCounter, LgInverter]]):
        nonlocal session_key
        session = req.get_http_session()
        try:
            response = _request_data(session, session_key, device_config.configuration.ip_address)
        except HTTPError:
            session_key = _update_session_key(
                session, device_config.configuration.ip_address, device_config.configuration.password)
            response = _request_data(session, session_key, device_config.configuration.ip_address)

        for component in components:
            with SingleComponentUpdateContext(component.fault_state):
                component.update(response)

    session_key = " "
    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=LG)
