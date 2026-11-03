#!/usr/bin/env python3
from modules.common import req
from typing import Optional
from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import ConsumerState
from modules.common.configurable_consumer import ConfigurableConsumer
from modules.consumers.shelly.shelly_pm.config import ShellyPM
from modules.devices.shelly.shelly.status_handler import get_generation, request_status, parse_data, parse_temperatures


def create_consumer(config: ShellyPM):
    model: Optional[str] = None
    generation: int = 1

    def initializer():
        nonlocal generation, model
        generation, model = get_generation(config.configuration.ip_address)

    def error_handler() -> None:
        initializer()

    def switch_on() -> None:
        if generation == 1:
            url = f"http://{config.configuration.ip_address}/relay/{config.configuration.channel}?turn=on"
        else:
            # shelly pro 3em mit add on hat fix id 100 als switch Kanal, das Device muss auf jeden fall mit separater
            # Leistunsmessung erfasst werden, da die Leistung auf drei verschiedenenen Kanälen angeliefert werden kann
            if "SPEM-003CE" in model:
                chan = 100
            else:
                chan = config.configuration.channel
            # gen 2 will das als on cmd /rpc/Switch.Set?id=100&on=true
            url = f"http://{config.configuration.ip_address}/rpc/Switch.Set?id={chan}&on=true"
        if config.configuration.username and config.configuration.password:
            auth = (config.configuration.username, config.configuration.password)
        else:
            auth = None
        req.get_http_session().get(url, auth=auth, timeout=3)

    def switch_off() -> None:
        if generation == 1:
            url = f"http://{config.configuration.ip_address}/relay/{config.configuration.channel}?turn=off"
        else:
            # shelly pro 3em mit add on hat fix id 100 als switch Kanal, das Device muss auf jeden fall mit separater
            # Leistunsmessung erfasst werden, da die Leistung auf drei verschiedenenen Kanälen angeliefert werden kann
            if "SPEM-003CE" in model:
                chan = 100
            else:
                chan = config.configuration.channel
            # gen 2 will das als on cmd /rpc/Switch.Set?id=100&on=true
            url = f"http://{config.configuration.ip_address}/rpc/Switch.Set?id={chan}&on=false"
        if config.configuration.username and config.configuration.password:
            auth = (config.configuration.username, config.configuration.password)
        else:
            auth = None
        req.get_http_session().get(url, auth=auth, timeout=3)

    def update() -> ConsumerState:
        status = request_status(config.configuration.ip_address, generation)
        powers, voltages, currents, _, power, _ = parse_data(1, config.configuration.factor, status)
        return ConsumerState(
            power=power,
            voltages=voltages,
            currents=currents,
            powers=powers,
            temperatures=parse_temperatures(status, generation),
        )

    return ConfigurableConsumer(consumer_config=config,
                                initializer=initializer,
                                error_handler=error_handler,
                                switch_on=switch_on,
                                switch_off=switch_off,
                                update=update,)


device_descriptor = DeviceDescriptor(configuration_factory=ShellyPM)
