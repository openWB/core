import logging
from pathlib import Path


log = logging.getLogger(__name__)

BUS_SOURCES = ("/dev/ttyUSB0", "/dev/ttyUSB1", "/dev/ttyACM0", "/dev/serial0")


def get_serial_modbus_devices():
    tty_devices = list(Path("/dev/serial/by-path").glob("*"))
    log.debug("tty_devices"+str(tty_devices))
    resolved_devices = [str(file.resolve()) for file in tty_devices]
    log.debug("resolved_devices"+str(resolved_devices))
    counter = len(resolved_devices)
    return resolved_devices, counter
