#!/usr/bin/env python3
from typing import Optional

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.consumers.heishamon.heishamon.config import HeishaMon

TEMPERATURE_NAMES = ("Main_Inlet_Temp", "Main_Outlet_Temp", "Main_Target_Temp")


def _temperature(value: object) -> Optional[float]:
    try:
        temperature = float(value)
    except (TypeError, ValueError):
        return None
    # Unbelegte Wassertemperatursensoren melden beispielsweise -128 oder -78 °C.
    return temperature if -50 <= temperature <= 100 else None


def create_consumer(config: HeishaMon):
    def update() -> ConsumerState:
        response = req.get_http_session().get(f"http://{config.configuration.ip_address}/json", timeout=5).json()
        values = {entry["Name"]: entry.get("Value") for entry in response["heatpump"]}

        # Nur die elektrische Heizleistung auswerten.
        name = "Heat_Power_Consumption"
        power = float(values[name])
        if power < 0:
            raise ValueError(
                f"Ungültiger Wert für HeishaMon-Feld '{name}': {power} W. "
                "Die Wärmepumpe liefert möglicherweise nur erweiterte Leistungswerte.")

        temperatures = [_temperature(values.get(name)) for name in TEMPERATURE_NAMES]
        return ConsumerState(power=power, temperatures=temperatures)

    return ConfigurableConsumer(consumer_config=config,
                                update=update)


device_descriptor = DeviceDescriptor(configuration_factory=HeishaMon)
