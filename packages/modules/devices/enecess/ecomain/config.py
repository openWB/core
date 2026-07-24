from typing import Optional

from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


class EcoMainConfiguration:
    def __init__(self, ip_address: Optional[str] = None, serial_number: Optional[str] = None):
        self.ip_address = ip_address
        self.serial_number = serial_number


class EcoMain:
    def __init__(self, name: str = "EcoMain", type: str = "ecomain", id: int = 0,
                 configuration: EcoMainConfiguration = None):
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or EcoMainConfiguration()


class EcoMainCounterConfiguration:
    def __init__(self):
        pass


class EcoMainCounterSetup(ComponentSetup[EcoMainCounterConfiguration]):
    def __init__(self, name: str = "EcoMain EVU-Zähler", type: str = "counter", id: int = 0,
                 configuration: EcoMainCounterConfiguration = None, **kwargs):
        super().__init__(name, type, id, configuration or EcoMainCounterConfiguration(), **kwargs)


class EcoMainChannelConfiguration:
    def __init__(self, phase: int = 1, source: int = 0, channel: int = 1):
        self.phase = phase
        self.source = source
        self.channel = channel


class EcoMainInverterConfiguration:
    def __init__(self, phase_count: int = 1, invert: bool = False,
                 channels: Optional[list[EcoMainChannelConfiguration]] = None):
        self.phase_count = phase_count
        self.invert = invert
        self.channels = channels if channels is not None else [EcoMainChannelConfiguration()]


class EcoMainInverterSetup(ComponentSetup[EcoMainInverterConfiguration]):
    def __init__(self, name: str = "EcoMain Wechselrichter", type: str = "inverter", id: int = 0,
                 configuration: EcoMainInverterConfiguration = None, **kwargs):
        super().__init__(name, type, id, configuration or EcoMainInverterConfiguration(), **kwargs)


def validate_inverter_configuration(
        configuration: EcoMainInverterConfiguration) -> list[EcoMainChannelConfiguration]:
    if configuration.phase_count not in (1, 3):
        raise ValueError("Die Phasenanzahl muss 1 oder 3 sein.")
    if len(configuration.channels) != configuration.phase_count:
        raise ValueError("Die Anzahl der EcoMain-Kanäle stimmt nicht mit der Phasenanzahl überein.")
    for item in configuration.channels:
        if item.phase not in (1, 2, 3):
            raise ValueError("Die Phase muss L1, L2 oder L3 sein.")
        if item.source not in (0, 1, 2, 3):
            raise ValueError("Die Quelle muss Hauptgerät oder Slave 1 bis 3 sein.")
        if not 1 <= item.channel <= 10:
            raise ValueError("Der EcoMain-Kanal muss zwischen 1 und 10 liegen.")
    if configuration.phase_count == 3 and {item.phase for item in configuration.channels} != {1, 2, 3}:
        raise ValueError("Bei dreiphasiger Messung müssen L1, L2 und L3 jeweils einmal konfiguriert sein.")
    physical_channels = {(item.source, item.channel) for item in configuration.channels}
    if len(physical_channels) != len(configuration.channels):
        raise ValueError("Eine EcoMain-Quelle und ein Kanal dürfen nicht mehrfach verwendet werden.")
    return sorted(configuration.channels, key=lambda item: item.phase)
