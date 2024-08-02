from modules.common.abstract_device import DeviceDescriptor
from modules.devices.vendors import VendorGroup


class Vendor:
    def __init__(self):
        self.vendor = "openEMS, Fenecon FEMS, CENTURIO, Kaco"
        self.group = VendorGroup.VENDORS.value


vendor_descriptor = DeviceDescriptor(configuration_factory=Vendor)
