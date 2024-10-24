#!/usr/bin/env python3
import logging
import requests
from requests import HTTPError
from typing import Iterable, Union

from modules.common.abstract_device import DeviceDescriptor
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.common.req import get_http_session
from modules.devices.tesla.tesla.bat import TeslaBat
from modules.devices.tesla.tesla.config import Tesla, TeslaBatSetup, TeslaCounterSetup, TeslaInverterSetup
from modules.devices.tesla.tesla.counter import TeslaCounter
from modules.devices.tesla.tesla.http_client import PowerwallHttpClient
from modules.devices.tesla.tesla.inverter import TeslaInverter

log = logging.getLogger(__name__)


def __update_components(client: PowerwallHttpClient,
                        components: Iterable[Union[TeslaBat, TeslaCounter, TeslaInverter]]):
    aggregate = client.get_json("/api/meters/aggregates")
    for component in components:
        component.update(client, aggregate)


def _authenticate(session: requests.Session, url: str, email: str, password: str):
    """
    email is not yet required for login (2022/01), but we simulate the whole login page
    """
    response = session.post(
        "https://" + url + "/api/login/Basic",
        json={"username": "customer", "email": email, "password": password, "force_sm_off": False},
        verify=False,
        timeout=5
    )
    log.debug("Authentication endpoint send cookies %s", str(response.cookies))
    return {"AuthCookie": response.cookies["AuthCookie"], "UserRecord": response.cookies["UserRecord"]}


def create_device(device_config: Tesla):
    def create_bat_component(component_config: TeslaBatSetup):
        return TeslaBat(component_config)

    def create_counter_component(component_config: TeslaCounterSetup):
        return TeslaCounter(component_config)

    def create_inverter_component(component_config: TeslaInverterSetup):
        return TeslaInverter(component_config)

    def update_components(components: Iterable[Union[TeslaBat, TeslaCounter, TeslaInverter]]):
        log.debug("Beginning update")
        nonlocal http_client
        address = device_config.configuration.ip_address
        email = device_config.configuration.email
        password = device_config.configuration.password

        if http_client.cookies is None:
            http_client.cookies = _authenticate(session, address, email, password)
            __update_components(http_client, components)
            return
        try:
            __update_components(http_client, components)
            return
        except HTTPError as e:
            if e.response.status_code != 401 and e.response.status_code != 403:
                raise e
            log.warning("Login to powerwall with existing cookie failed. Will retry with new cookie...")
        http_client.cookies = _authenticate(session, address, email, password)
        __update_components(http_client, components)
        log.debug("Update completed successfully")

    session = get_http_session()
    http_client = PowerwallHttpClient(device_config.configuration.ip_address, session, None)
    return ConfigurableDevice(
        device_config=device_config,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=Tesla)
