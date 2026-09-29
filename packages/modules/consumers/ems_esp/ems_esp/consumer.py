#!/usr/bin/env python3
import logging
from typing import Optional

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.component_type import ComponentType
from modules.common.configurable_consumer import ConfigurableConsumer, SetLimitData
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.ems_esp.ems_esp.config import EmsEsp

log = logging.getLogger(__name__)


def create_consumer(config: EmsEsp):
    session: Optional[req.CustomSession] = None
    sim_counter: Optional[SimCounterConsumer] = None
    base_url: str = ""
    headers: dict = {}

    def initializer():
        nonlocal session, sim_counter, base_url, headers
        session = req.get_http_session()
        sim_counter = SimCounterConsumer(config.id, ComponentType.CONSUMER)
        # "heatpump" ist der EMS-ESP-Gerätename für eine reine Wärmepumpe; Hybridanlagen mit
        # Gas-/Ölkessel laufen zB unter "boiler" (https://emsesp.org/All-Entities).
        base_url = f"http://{config.configuration.ip_address}/api/heatpump"
        headers = {"Content-Type": "application/json",
                   "Authorization": f"Bearer {config.configuration.token}"}

    def _write_entity(entity: str, value) -> None:
        session.post(f"{base_url}/{entity}", json={"value": value}, headers=headers)

    def switch_on() -> None:
        _write_entity("hpin4opt", "1xxxxxxxxxxx")

    def switch_off() -> None:
        _write_entity("hpin4opt", "0xxxxxxxxxxx")
        _write_entity("hpin1opt", "0xxxxxxxxxxxxxx")

    def update() -> ConsumerState:
        # fehlender Schlüssel (zB falsches Modell) kommt als 200 OK zurück, nicht als HTTP-Fehler -
        # ohne diese Prüfung würde das unbemerkt als 0W durchgehen.
        values = session.get(base_url, headers=headers).json()
        if "hpcurrpower" not in values:
            raise ValueError(
                f"Entity 'hpcurrpower' nicht in der Antwort von {base_url} enthalten - "
                f"vorhandene Werte: {list(values.keys())}")
        power = float(values["hpcurrpower"])
        imported, exported = sim_counter.sim_count(power)

        return ConsumerState(
            power=power,
            imported=imported,
            exported=exported
        )

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
