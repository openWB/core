from helpermodules.auto_str import auto_str

from modules.common.abstract_device import DeviceDescriptor


@auto_str
class StandardWebThemeConfiguration:
    def __init__(self) -> None:
        pass


@auto_str
class StandardWebTheme:
    def __init__(self,
                 name: str = "Standard (in Entwicklung)",
                 type: str = "standard",
                 official: bool = True,
                 configuration: StandardWebThemeConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or StandardWebThemeConfiguration()


theme_descriptor = DeviceDescriptor(configuration_factory=StandardWebTheme)
