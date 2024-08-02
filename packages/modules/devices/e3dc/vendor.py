from modules.common.abstract_device import DeviceDescriptor
from modules.devices.vendors import VendorGroup


class Vendor:
    def __init__(self):
        self.vendor = "E3/DC"
        self.group = VendorGroup.VENDORS.value


vendor_descriptor = DeviceDescriptor(configuration_factory=Vendor)
