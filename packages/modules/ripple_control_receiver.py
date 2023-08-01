import logging
import time
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
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(8, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(9, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        try:
            button1_state = GPIO.input(8)
            button2_state = GPIO.input(9)

            time.sleep(10.2)

            rse1 = not button1_state
            rse2 = not button2_state
        except Exception:
            GPIO.cleanup()
            log.exception("Fehler beim Auslesen der Rundsteuer-Kontakte.")
    return rse1, rse2
