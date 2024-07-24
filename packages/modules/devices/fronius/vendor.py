from modules.common.abstract_device import DeviceDescriptor


class Vendor:
    def __init__(self):
        self.vendor = "Fronius"


vendor_descriptor = DeviceDescriptor(configuration_factory=Vendor)
