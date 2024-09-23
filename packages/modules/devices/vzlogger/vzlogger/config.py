from typing import Optional

from helpermodules.auto_str import auto_str
from modules.common.component_setup import ComponentSetup
from ..vendor import vendor_descriptor


@auto_str
class VZLoggerConfiguration:
    def __init__(self, ip_address: Optional[str] = None):
        self.ip_address = ip_address


@auto_str
class VZLogger:
    def __init__(self,
                 name: str = "VZLogger",
                 type: str = "vzlogger",
                 id: int = 0,
                 configuration: VZLoggerConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.vendor = vendor_descriptor.configuration_factory().type
        self.id = id
        self.configuration = configuration or VZLoggerConfiguration()


@auto_str
class VZLoggerCounterConfiguration:
    def __init__(self, line_power: int = 0, line_exported: Optional[int] = None, line_imported: Optional[int] = None):
        self.line_power = line_power
        self.line_exported = line_exported
        self.line_imported = line_imported


@auto_str
class VZLoggerCounterSetup(ComponentSetup[VZLoggerCounterConfiguration]):
    def __init__(self,
                 name: str = "VZLogger Zähler",
                 type: str = "counter",
                 id: int = 0,
                 configuration: VZLoggerCounterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or VZLoggerCounterConfiguration())


@auto_str
class VZLoggerInverterConfiguration:
    def __init__(self, line_power: int = 0, line_exported: Optional[int] = None):
        self.line_power = line_power
        self.line_exported = line_exported


@auto_str
class VZLoggerInverterSetup(ComponentSetup[VZLoggerInverterConfiguration]):
    def __init__(self,
                 name: str = "VZLogger Wechselrichter",
                 type: str = "inverter",
                 id: int = 0,
                 configuration: VZLoggerInverterConfiguration = None) -> None:
        super().__init__(name, type, id, configuration or VZLoggerInverterConfiguration())
