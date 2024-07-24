from modules.common.abstract_device import DeviceDescriptor


class Vendor:
    def __init__(self, vendor: str = "byd"):
        self.vendor = vendor


vendor_descriptor = DeviceDescriptor(configuration_factory=Vendor)
