#!/usr/bin/env python3
import logging
import requests
from requests import HTTPError
from typing import Iterable, Union, Optional

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import ComponentFactoryByType, ConfigurableDevice, MultiComponentUpdater
from modules.common.req import get_http_session
from modules.devices.tesla.tesla.bat import TeslaBat
from modules.devices.tesla.tesla.config import Tesla, TeslaBatSetup, TeslaCounterSetup, TeslaInverterSetup
from modules.devices.tesla.tesla.counter import TeslaCounter
from modules.devices.tesla.tesla.http_client import PowerwallHttpClient
from modules.devices.tesla.tesla.inverter import TeslaInverter

log = logging.getLogger(__name__)


def __update_components(
    client: PowerwallHttpClient,
    components: Iterable[Union[TeslaBat, TeslaCounter, TeslaInverter]],
):
    aggregate = client.get_json("/api/meters/aggregates")

    for component in components:
        try:
            # For Tesla/Powerwall we want fail-fast behaviour:
            # if one critical component update fails (especially EVU / house transition point),
            # abort the remaining Tesla component updates in this cycle.
            with SingleComponentUpdateContext(component.fault_state, reraise=True):
                component.update(client, aggregate)
        except Exception:
            break


def _authenticate(session: requests.Session, url: str, email: str, password: str):
    """
    email is not yet required for login (2022/01), but we simulate the whole login page
    """
    response = session.post(
        "https://" + url + "/api/login/Basic",
        json={"username": "customer", "email": email, "password": password, "force_sm_off": False},
        verify=False,
        timeout=5,
    )
    response.raise_for_status()

    return {"AuthCookie": response.cookies["AuthCookie"], "UserRecord": response.cookies["UserRecord"]}


def create_device(device_config: Tesla):
    http_client: Optional[PowerwallHttpClient] = None
    session: Optional[requests.Session] = None

    def create_bat_component(component_config: TeslaBatSetup):
        return TeslaBat(component_config)

    def create_counter_component(component_config: TeslaCounterSetup):
        return TeslaCounter(component_config)

    def create_inverter_component(component_config: TeslaInverterSetup):
        return TeslaInverter(component_config)

							  
									 
												  
						 
												  
																							  

    def update_components(components: Iterable[Union[TeslaBat, TeslaCounter, TeslaInverter]]):
        nonlocal http_client, session

        address = device_config.configuration.ip_address
        email = device_config.configuration.email
        password = device_config.configuration.password

							 

																   
								 

        # First run after process start: no cookies -> authenticate once
        if http_client.cookies is None:
            http_client.cookies = _authenticate(session, address, email, password)
											 
            __update_components(http_client, components)
            return

        # Normal operation: reuse cookie. If it fails with 401/403 -> re-auth
        try:
            __update_components(http_client, components)
            return
        except HTTPError as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status not in (401, 403):
                raise
            log.warning(
                "Login to powerwall with existing cookie failed (status=%s). Will retry with new cookie...",
                status,
            )

        http_client.cookies = _authenticate(session, address, email, password)
										 
        __update_components(http_client, components)

    def initializer():
        nonlocal http_client, session
        session = get_http_session()
        http_client = PowerwallHttpClient(device_config.configuration.ip_address, session, None)

    return ConfigurableDevice(
        device_config=device_config,
        initializer=initializer,
        component_factory=ComponentFactoryByType(
            bat=create_bat_component,
            counter=create_counter_component,
            inverter=create_inverter_component,
        ),
        component_updater=MultiComponentUpdater(update_components),
    )


device_descriptor = DeviceDescriptor(configuration_factory=Tesla)
