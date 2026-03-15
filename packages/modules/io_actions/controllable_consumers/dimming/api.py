import logging
from modules.common.abstract_device import DeviceDescriptor
from modules.io_actions.controllable_consumers.dimming.api_eebus import DimmingEebus
from modules.io_actions.controllable_consumers.dimming.api_io import DimmingIo
from modules.io_actions.controllable_consumers.dimming.config import DimmingSetup

log = logging.getLogger(__name__)


def create_action(config: DimmingSetup, parent_device_type: str):
    if config.configuration.io_device is None:
        log.debug("Dimmen per EMS: Kein IO-Gerät konfiguriert.")
    if parent_device_type == "eebus":
        return DimmingEebus(config=config)
    else:
        return DimmingIo(config=config)


device_descriptor = DeviceDescriptor(configuration_factory=DimmingSetup)
