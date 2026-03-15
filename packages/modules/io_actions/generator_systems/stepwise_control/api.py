import logging
from modules.common.abstract_device import DeviceDescriptor
from modules.io_actions.generator_systems.stepwise_control.api_eebus import StepwiseControlEebus
from modules.io_actions.generator_systems.stepwise_control.api_io import StepwiseControlIo
from modules.io_actions.generator_systems.stepwise_control.config import StepwiseControlSetup

log = logging.getLogger(__name__)


def create_action(config: StepwiseControlSetup, parent_device_type: str):
    if config.configuration.io_device is None:
        log.debug("Stufenweise Steuerung von EZA: Kein IO-Gerät konfiguriert.")
    if parent_device_type == "eebus":
        return StepwiseControlEebus(config=config)
    else:
        return StepwiseControlIo(config=config)


device_descriptor = DeviceDescriptor(configuration_factory=StepwiseControlSetup)
