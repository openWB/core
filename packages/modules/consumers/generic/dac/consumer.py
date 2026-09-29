#!/usr/bin/env python3
import logging
from typing import Optional
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_type import ComponentType
from modules.common.configurable_consumer import ConfigurableConsumer, SetLimitData
from modules.common.modbus import ModbusTcpClient_
from modules.common.simcount._simcounter import SimCounterConsumer
from modules.consumers.generic.dac.config import Dac
from modules.consumers.generic.dac.model import Model

log = logging.getLogger(__name__)


def create_consumer(config: Dac):
    client: Optional[ModbusTcpClient_] = None
    sim_counter: Optional[SimCounterConsumer] = None

    def initializer():
        nonlocal client, sim_counter
        client = ModbusTcpClient_(config.configuration.ip_address, config.configuration.port)
        sim_counter = SimCounterConsumer(config.id, ComponentType.CONSUMER)

    def error_handler() -> None:
        initializer()

    def set_power_limit(power_limit: float, data: SetLimitData) -> None:
        power_limit = max(power_limit, 0)
        modbus_id = config.configuration.modbus_id
        try:
            model_settings = Model[config.configuration.model].value
        except KeyError:
            raise ValueError(f"Unknown DAC model: {config.configuration.model}")

        # signal range calculation
        min_value = model_settings["min_value"]
        max_value = model_settings["max_value"]
        signal_range = max_value - min_value
        if not config.configuration.full_signal_range:
            min_value = round(min_value + signal_range * model_settings["output_type"].value["live_zero_factor"])
            signal_range *= (1 - model_settings["output_type"].value["live_zero_factor"])

        # power mapping to signal range
        mapped_power_limit = round(min_value + (power_limit / data.max_power) * signal_range)
        mapped_power_limit = max(min(mapped_power_limit, max_value), min_value)

        # modbus write
        client.write_register(model_settings["register"], mapped_power_limit,
                              model_settings["data_type"], unit=modbus_id)

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                error_handler=error_handler,
                                set_power_limit=set_power_limit)


device_descriptor = DeviceDescriptor(configuration_factory=Dac)
