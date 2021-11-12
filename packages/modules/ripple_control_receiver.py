import RPi.GPIO as GPIO
import time

from ..helpermodules import log
from ..helpermodules import pub


def read_ripple_control_receiver():

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(8, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    GPIO.setup(9, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    try:
        button1_state = GPIO.input(8)
        button2_state = GPIO.input(9)

        time.sleep(10.2)

        if button1_state is False:
            pub.pub("openWB/set/general/ripple_control_receiver/r1_active", True)
            time.sleep(0.2)
        else:
            pub.pub("openWB/set/general/ripple_control_receiver/r1_active", False)
            time.sleep(0.2)
        if button2_state is False:
            pub.pub("openWB/set/general/ripple_control_receiver/r2_active", True)
            time.sleep(0.2)
        else:
            pub.pub("openWB/set/general/ripple_control_receiver/r2_active", False)
            time.sleep(0.2)
    except Exception as e:
        GPIO.cleanup()
        log.exception_logging(e)
