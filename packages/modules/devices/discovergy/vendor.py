from pathlib import Path

from modules.common.abstract_device import DeviceDescriptor
from modules.devices.vendors import VendorGroup


class Vendor:
    def __init__(self):
        self.type = Path(__file__).parent.name
        self.vendor = "inexogy (Discovergy)"
        self.group = VendorGroup.VENDORS.value


vendor_descriptor = DeviceDescriptor(configuration_factory=Vendor)
