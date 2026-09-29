#!/usr/bin/env python3
import logging
from typing import Union, Iterable
import hmac
import hashlib
import time
import uuid
from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.configurable_device import (ConfigurableDevice, ComponentFactoryByType,
                                                MultiComponentUpdater)
from modules.devices.ecoflow.stream.bat import EcoflowStreamBat
from modules.devices.ecoflow.stream.config import (EcoflowStream,
                                                   EcoflowStreamBatSetup,
                                                   EcoflowStreamCounterSetup,
                                                   EcoflowStreamInverterSetup)
from modules.devices.ecoflow.stream.counter import EcoflowStreamCounter
from modules.devices.ecoflow.stream.inverter import EcoflowStreamInverter

log = logging.getLogger(__name__)
EcoflowStreamComponent = Union[EcoflowStreamBat, EcoflowStreamCounter, EcoflowStreamInverter]


def create_device(device_config: EcoflowStream):
    def create_bat(component_config: EcoflowStreamBatSetup) -> EcoflowStreamBat:
        return EcoflowStreamBat(component_config=component_config, device_id=device_config.id)

    def create_counter(component_config: EcoflowStreamCounterSetup) -> EcoflowStreamCounter:
        return EcoflowStreamCounter(component_config=component_config, device_id=device_config.id)

    def create_inverter(component_config: EcoflowStreamInverterSetup) -> EcoflowStreamInverter:
        return EcoflowStreamInverter(component_config=component_config, device_id=device_config.id)

    def generate_sign(access_key, secret_key, timestamp, nonce):
        message = f"accessKey={access_key}&nonce={nonce}&timestamp={timestamp}"
        sign = hmac.new(
            secret_key.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()
        return sign

    def update_components(components: Iterable[EcoflowStreamComponent]):
        access_key = device_config.configuration.access_key
        secret_key = device_config.configuration.secret_key
        serial = device_config.configuration.serial
        base_url = "https://api-e.ecoflow.com"

        timestamp = str(int(time.time() * 1000))
        nonce = str(uuid.uuid4())
        sign = generate_sign(access_key, secret_key, timestamp, nonce)

        headers = {
            "accessKey": access_key,
            "timestamp": timestamp,
            "nonce": nonce,
            "sign": sign,
            "Content-Type": "application/json"
        }
        url = f"{base_url}/iot-open/sign/device/quota/all?sn={serial}"

        response = req.get_http_session().get(
            url,
            headers=headers,
            timeout=10
        ).json()
        for component in components:
            with SingleComponentUpdateContext(component.fault_state):
                component.update(response)

    return ConfigurableDevice(
        device_config,
        component_factory=ComponentFactoryByType(bat=create_bat, counter=create_counter, inverter=create_inverter),
        component_updater=MultiComponentUpdater(update_components)
    )


device_descriptor = DeviceDescriptor(configuration_factory=EcoflowStream)
