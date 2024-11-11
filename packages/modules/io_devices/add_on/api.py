#!/usr/bin/env python3
import logging
from typing import Dict, Tuple

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import IoState
from modules.common.configurable_io import ConfigurableIo
from modules.io_devices.add_on.config import AddOn

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
            return IoState(digital_input={"21": GPIO.input(21) == GPIO.LOW,
                                          "24": GPIO.input(24) == GPIO.LOW,
                                          "31": GPIO.input(31) == GPIO.LOW,
                                          "32": GPIO.input(32) == GPIO.LOW,
                                          "33": GPIO.input(33) == GPIO.LOW,
                                          "36": GPIO.input(36) == GPIO.LOW,
                                          "40": GPIO.input(40) == GPIO.LOW})
        else:
            return IoState()

    def write(digital_output: Dict[int, int]):
        if has_gpio:
            for i, value in digital_output.items():
                GPIO.output(i, GPIO.HIGH if value else GPIO.LOW)
            return IoState(dict(digital_output=digital_output))

    if has_gpio:
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # RSE 2
        GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # RSE 1
        GPIO.setup(31, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Taster 3 PV
        GPIO.setup(32, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Taster 1 Sofortladen
        GPIO.setup(33, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Taster 4 Stop
        GPIO.setup(36, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # Taster 2 Min+PV
        GPIO.setup(40, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # TAster 5 Standby
        GPIO.setup(7, GPIO.OUT, pull_up_down=GPIO.PUD_UP if config.output["digital"]["7"] else GPIO.PUD_DOWN)    # LED 3
        GPIO.setup(16, GPIO.OUT, pull_up_down=GPIO.PUD_UP if config.output["digital"]["16"] else GPIO.PUD_DOWN)  # LED 2
        GPIO.setup(18, GPIO.OUT, pull_up_down=GPIO.PUD_UP if config.output["digital"]["18"] else GPIO.PUD_DOWN)  # LED 1

    return ConfigurableIo(config=config, component_reader=read, component_writer=write)


device_descriptor = DeviceDescriptor(configuration_factory=AddOn)
