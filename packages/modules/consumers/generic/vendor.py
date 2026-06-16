from pathlib import Path

from modules.common.abstract_device import DeviceDescriptor
from modules.devices.vendors import VendorGroup


class Vendor:
    def __init__(self):
        self.type = Path(__file__).parent.name
        self.vendor = "Universell"
        self.group = VendorGroup.GENERIC.value


vendor_descriptor = DeviceDescriptor(configuration_factory=Vendor)
