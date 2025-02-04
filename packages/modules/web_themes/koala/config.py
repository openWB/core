from helpermodules.auto_str import auto_str

from modules.common.abstract_device import DeviceDescriptor


@auto_str
class KoalaWebThemeConfiguration:
    def __init__(self) -> None:
        pass


@auto_str
class KoalaWebTheme:
    def __init__(self,
                 name: str = "Koala (in Entwicklung)",
                 type: str = "koala",
                 official: bool = True,
                 configuration: KoalaWebThemeConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or KoalaWebThemeConfiguration()


theme_descriptor = DeviceDescriptor(configuration_factory=KoalaWebTheme)
