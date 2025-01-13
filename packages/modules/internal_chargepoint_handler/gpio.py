import copy
import logging
from threading import Event
import time

from helpermodules.subdata import SubData


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
                        io = SubData.system_data["iolocal"]
                        self.event_restart_gpio.clear()
                    data = copy.deepcopy(SubData.io_states)
                    log.debug(data)
                    log.setLevel(SubData.system_data["system"].data["debug_level"])
                    io.read()
                    io.store.update()
                    if "internal_io_states" in data:
                        io.write(data["internal_io_states"].data.set.digital_output)
                time.sleep(3)
