import logging
from typing import Tuple

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
        except Exception:
            GPIO.cleanup()
            log.exception("Fehler beim Auslesen der Rundsteuer-Kontakte.")
    log.debug(f"RSE1-Status: {rse1}, RSE2-Status: {rse2}")
    return rse1, rse2
