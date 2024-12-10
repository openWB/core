import copy
import logging
from threading import Event
import time

from helpermodules.subdata import SubData
from modules.internal_chargepoint_handler.add_on.api import create_io


log = logging.getLogger(__name__)
has_gpio = True


class InternalGpioHandler:
    def __init__(self, event_restart_gpio: Event):
        self.event_restart_gpio = event_restart_gpio

    def loop(self):
        if has_gpio:
            while True:
                if SubData.system_data.get("iolocal") is not None:
                    if self.event_restart_gpio.is_set():
                        io = create_io(SubData.system_data["iolocal"])
                        self.event_restart_gpio.clear()
                    data = copy.deepcopy(SubData.io_states)
                    log.debug(data)
                    log.setLevel(SubData.system_data["system"].data["debug_level"])
                    io.read()
                    io.store.update()
                    io.write(data["local"].data.set.digital_output)
                time.sleep(3)
