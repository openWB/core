from helpermodules.auto_str import auto_str

from modules.common.abstract_device import DeviceDescriptor


@auto_str
class ColorsWebThemeConfiguration:
    def __init__(self) -> None:
        pass


@auto_str
class ColorsWebTheme:
    def __init__(self,
                 name: str = "Colors",
                 type: str = "colors",
                 configuration: ColorsWebThemeConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.configuration = configuration or ColorsWebThemeConfiguration()


theme_descriptor = DeviceDescriptor(configuration_factory=ColorsWebTheme)
