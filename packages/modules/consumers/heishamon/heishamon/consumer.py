#!/usr/bin/env python3
from math import isfinite
from typing import Dict, Optional

from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.consumers.heishamon.heishamon.config import HeishaMon

TEMPERATURE_NAMES = ("Main_Inlet_Temp", "Main_Outlet_Temp", "Main_Target_Temp")


def _get_number(value: object, name: str) -> float:
    try:
        if isinstance(value, bool):
            raise ValueError
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        raise ValueError(f"Kein gültiger Zahlenwert für HeishaMon-Feld '{name}'.") from None
    if not isfinite(number):
        raise ValueError(f"Kein endlicher Zahlenwert für HeishaMon-Feld '{name}'.")
    return number


def _get_temperature(values: Dict[str, object], name: str) -> Optional[float]:
    try:
        temperature = _get_number(values.get(name), name)
    except ValueError:
        return None
    # Water temperatures only: exclude disconnected sensor values such as -128 and -78 °C.
    return temperature if -50 <= temperature <= 100 else None


def create_consumer(config: HeishaMon):
    session: Optional[req.CustomSession] = None

    def initializer():
        nonlocal session
        session = req.get_http_session()

    def update() -> ConsumerState:
        response = session.get(f"http://{config.configuration.ip_address}/json", timeout=5).json()
        if not isinstance(response, dict) or not isinstance(response.get("heatpump"), list):
            raise ValueError("HeishaMon-Antwort enthält keine 'heatpump'-Liste.")
        values = {entry["Name"]: entry.get("Value") for entry in response["heatpump"]
                  if isinstance(entry, dict) and isinstance(entry.get("Name"), str)}

        # Deliberately use only this electrical consumption field, not thermal production
        # or a sum across operating modes. Other HeishaMon power layouts are not supported here.
        name = "Heat_Power_Consumption"
        power = _get_number(values.get(name), name)
        if power < 0:
            raise ValueError(
                f"Ungültiger Wert für HeishaMon-Feld '{name}': {power} W. "
                "Die Wärmepumpe liefert möglicherweise nur erweiterte Leistungswerte.")

        # Keep fixed positions even when one optional sensor is missing or invalid.
        temperatures = ([_get_temperature(values, name) for name in TEMPERATURE_NAMES]
                        if config.configuration.read_temperatures else None)
        return ConsumerState(power=power, temperatures=temperatures)

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                update=update)


device_descriptor = DeviceDescriptor(configuration_factory=HeishaMon)
