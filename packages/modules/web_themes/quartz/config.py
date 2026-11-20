from helpermodules.auto_str import auto_str

from modules.common.abstract_device import DeviceDescriptor


@auto_str
class QuartzWebThemeConfiguration:
    def __init__(self) -> None:
        pass


@auto_str
class QuartzWebTheme:
    def __init__(self,
                 name: str = "Quartz",
                 type: str = "quartz",
                 official: bool = False,
                 userManagementSupported: bool = True,
                 configuration: QuartzWebThemeConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.userManagementSupported = userManagementSupported
        self.configuration = configuration or QuartzWebThemeConfiguration()


theme_descriptor = DeviceDescriptor(configuration_factory=QuartzWebTheme)
