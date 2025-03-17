#!/usr/bin/env python3
import logging
from typing import Dict, Optional, Tuple

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import IoState
from modules.common.configurable_io import ConfigurableIo
from modules.common.store._io_internal import get_internal_io_value_store
from modules.io_devices.add_on.config import AddOn, DigitalInputMapping, DigitalOutputMapping

log = logging.getLogger(__name__)
has_gpio = True

try:
    import RPi.GPIO as GPIO
except ImportError:
    has_gpio = False
    log.info("failed to import RPi.GPIO! maybe we are not running on a pi")
    log.warning("RSE disabled!")


def create_io(config: AddOn):
    def read() -> Tuple[bool, bool]:
        if has_gpio:
            return IoState(
                digital_input={input.name: GPIO.input(input.value) == GPIO.LOW for input in DigitalInputMapping},
                digital_output={output.name: GPIO.input(output.value) == GPIO.LOW for output in DigitalOutputMapping})
        else:
            return IoState()

    def write(analog_output: Optional[Dict[str, int]], digital_output: Optional[Dict[str, bool]]):
        if has_gpio:
            for pin, value in digital_output.items():
                GPIO.output(DigitalOutputMapping[pin].value, GPIO.HIGH if value else GPIO.LOW)

    if has_gpio:
        GPIO.setmode(GPIO.BOARD)
        for pin in config.input["digital"].keys():
            GPIO.setup(DigitalInputMapping[pin].value, GPIO.IN)
        GPIO.setup([7, 16, 18], GPIO.OUT)

    io = ConfigurableIo(config=config, component_reader=read, component_writer=write)
    io.store = get_internal_io_value_store()
    return io


device_descriptor = DeviceDescriptor(configuration_factory=AddOn)
