from modules.common.abstract_device import DeviceDescriptor


class Vendor:
    def __init__(self, vendor: str = "E3/DC"):
        self.vendor = vendor


vendor_descriptor = DeviceDescriptor(configuration_factory=Vendor)
