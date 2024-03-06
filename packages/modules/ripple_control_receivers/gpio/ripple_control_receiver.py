#!/usr/bin/env python3
import logging
from typing import Tuple

from modules.common.abstract_device import DeviceDescriptor
from modules.common.component_state import RcrState
from modules.ripple_control_receivers.gpio.config import GpioRcr

log = logging.getLogger(__name__)
has_gpio = True

try:
    import RPi.GPIO as GPIO
except ImportError:
    has_gpio = False
    log.info("failed to import RPi.GPIO! maybe we are not running on a pi")
    log.warning("RSE disabled!")


def read() -> Tuple[bool, bool]:
    rse1: bool = False
    rse2: bool = False

    if has_gpio:
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(24, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(21, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        try:
            rse1 = GPIO.input(24) == GPIO.LOW
            rse2 = GPIO.input(21) == GPIO.LOW
        except Exception as e:
            GPIO.cleanup()
            raise e
    log.debug(f"RSE-Kontakt 1: {rse1}, RSE-Kontakt 2: {rse2}")
    if rse1 or rse2:
        override_value = 0
    else:
        override_value = 100
    return RcrState(override_value=override_value)


def create_ripple_control_receiver(config: GpioRcr):
    def updater():
        return read()
    return updater


device_descriptor = DeviceDescriptor(configuration_factory=GpioRcr)
