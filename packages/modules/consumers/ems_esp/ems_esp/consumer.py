#!/usr/bin/env python3
import logging
from typing import Optional

import requests

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.configurable_consumer import ConfigurableConsumer, SetLimitData
from modules.consumers.ems_esp.ems_esp.config import EmsEsp

log = logging.getLogger(__name__)

# EMS-ESP führt eine reine Wärmepumpe nicht zwingend unter "heatpump" (ursprüngliche Annahme
# dieses Moduls) - zB Bosch Compress 6800i liegt unter "boiler", eigentlich für Gasthermen o.ä.
# gedacht (Issue #4282).
DEVICE_NAMES = ("heatpump", "boiler")


def create_consumer(config: EmsEsp):
    session: Optional[req.CustomSession] = None
    base_url: Optional[str] = None
    headers: dict = {}

    def initializer():
        nonlocal session, headers
        session = req.get_http_session()
        headers = {"Content-Type": "application/json",
                   "Authorization": f"Bearer {config.configuration.token}"}

    def _detect_base_url() -> str:
        for device_name in DEVICE_NAMES:
            url = f"http://{config.configuration.ip_address}/api/{device_name}"
            try:
                values = session.get(url, headers=headers).json()
            except requests.exceptions.HTTPError as e:
                if e.response is not None and e.response.status_code == 404:
                    continue
                raise
            if "hpcurrpower" in values:
                return url
        raise ValueError(
            f"Keine Wärmepumpen-Entity 'hpcurrpower' unter {DEVICE_NAMES} auf "
            f"{config.configuration.ip_address} gefunden.")

    def _get_base_url() -> str:
        nonlocal base_url
        if base_url is None:
            base_url = _detect_base_url()
        return base_url

    def _write_entity(entity: str, value) -> None:
        session.post(f"{_get_base_url()}/{entity}", json={"value": value}, headers=headers)

    def switch_on() -> None:
        _write_entity("hpin4opt", "1xxxxxxxxxxx")

    def switch_off() -> None:
        _write_entity("hpin4opt", "0xxxxxxxxxxx")
        _write_entity("hpin1opt", "0xxxxxxxxxxxxxx")

    def update() -> ConsumerState:
        url = _get_base_url()
        # fehlender Schlüssel (zB falsches Modell) kommt als 200 OK zurück, nicht als HTTP-Fehler -
        # ohne diese Prüfung würde das unbemerkt als 0W durchgehen.
        values = session.get(url, headers=headers).json()
        if "hpcurrpower" not in values:
            raise ValueError(
                f"Entity 'hpcurrpower' nicht in der Antwort von {url} enthalten - "
                f"vorhandene Werte: {list(values.keys())}")
        power = float(values["hpcurrpower"])
        return ConsumerState(power=power)

    def set_power_limit(power_limit: Optional[float], data: SetLimitData) -> None:
        # pvmaxcomp wirkt nur bei aktivem SG-Ready-Boost (Eingang 4); bei SUSPENDABLE_TUNABLE ruft
        # der Core nie switch_on, daher hier selbst mitschalten. Wirksamkeit von pvmaxcomp ist
        # modellabhängig (EMS-ESP32 Diskussion #2062: funktioniert auf Buderus WLW186i-12E, nicht
        # auf Bosch Compress CS7000iAW).
        if power_limit is None:
            _write_entity("hpin4opt", "0xxxxxxxxxxx")
            _write_entity("hpin1opt", "0xxxxxxxxxxxxxx")
        else:
            _write_entity("hpin4opt", "1xxxxxxxxxxx")
            _write_entity("pvmaxcomp", round(max(power_limit, 0) / 1000, 1))

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                update=update,
                                set_power_limit=set_power_limit,
                                switch_on=switch_on,
                                switch_off=switch_off)


device_descriptor = DeviceDescriptor(configuration_factory=EmsEsp)
