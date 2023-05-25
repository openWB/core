from helpermodules.auto_str import auto_str

from modules.common.abstract_device import DeviceDescriptor


@auto_str
class CardsWebThemeConfiguration:
    def __init__(self) -> None:
        pass


@auto_str
class CardsWebTheme:
    def __init__(self,
                 name: str = "Standard",
                 type: str = "standard",
                 configuration: CardsWebThemeConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or CardsWebThemeConfiguration()


theme_descriptor = DeviceDescriptor(configuration_factory=CardsWebTheme)
