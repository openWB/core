from modules.common.abstract_device import DeviceDescriptor


class Vendor:
    def __init__(self):
        self.vendor = "QCells"


vendor_descriptor = DeviceDescriptor(configuration_factory=Vendor)
