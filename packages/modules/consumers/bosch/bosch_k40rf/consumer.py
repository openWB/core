#!/usr/bin/env python3
import logging
from typing import Optional

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.consumers.bosch.bosch_k40rf.config import BoschK40Rf

log = logging.getLogger(__name__)


def _extract_value(payload):
    return payload["value"] if isinstance(payload, dict) and "value" in payload else payload


def create_consumer(config: BoschK40Rf):
    session: Optional[req.CustomSession] = None
    base_url = f"https://{config.configuration.ip_address}:{config.configuration.port}"

    def initializer():
        nonlocal session
        session = req.get_http_session()
        session.headers.update({"Authorization": f"Bearer {config.configuration.token}"})

    def _get(path: str):
        return _extract_value(session.get(base_url + path, verify=False).json())

    def update() -> ConsumerState:
        power = _get("/heatSources/compressor/powerElecActual")
        try:
            power += _get("/heatSources/eHeater/powerElecActual")
        except Exception:
            pass
        consumption = _get("/heatSources/emon/totalConsumption")
        imported = consumption["electricity"] * 1000
        return ConsumerState(power=power, imported=imported)

    return ConfigurableConsumer(consumer_config=config, initializer=initializer, update=update)


device_descriptor = DeviceDescriptor(configuration_factory=BoschK40Rf)
