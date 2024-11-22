import logging
import time

from modules.internal_chargepoint_handler.add_on.api import create_io
from modules.internal_chargepoint_handler.add_on.config import AddOn


log = logging.getLogger(__name__)
has_gpio = True

try:
    import RPi.GPIO as GPIO
except ImportError:
    has_gpio = False
    log.info("failed to import RPi.GPIO! maybe we are not running on a pi")
    log.warning("RSE disabled!")


class InternalGpioHandler:
    def __init__(self):
        if has_gpio:
            GPIO.setmode(GPIO.BOARD)
            input_pins = [21, 24, 31, 32, 33, 36, 40]
            # 21: RSE 2
            # 24: RSE 1
            # 31: Taster 3 PV
            # 32: Taster 1 Sofortladen
            # 33: Taster 4 Stop
            # 36: Taster 2 Min+PV
            # 40: Taster 5 Standby
            GPIO.setup(input_pins, GPIO.IN, pull_up_down=GPIO.PUD_UP)

            self.io = create_io(AddOn(id="local"))

    def loop(self):
        if has_gpio:
            while True:
                self.io.read()
                self.io.store.update()
                time.sleep(3)
