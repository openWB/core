class Smarthome:
    def __init__(self):
        self.device = Device()

    def initialize():
        self.store = get_store_topcis_smarthome()

    def update(self):
        self.device.update()


class Device:
    def initialize():
        self.store = get_store_topcis_device()

    def update(self):
        # reuest values
        self.store.set_values()
