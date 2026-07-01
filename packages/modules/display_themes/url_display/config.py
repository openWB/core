from helpermodules.auto_str import auto_str

from modules.common.abstract_device import DeviceDescriptor


@auto_str
class UrlDisplayThemeConfiguration:
    def __init__(self,
                 url: str = "http://www.example.com"
                 ) -> None:
        self.url = url


@auto_str
class UrlDisplayTheme:
    def __init__(self,
                 name: str = "URL Display",
                 type: str = "url_display",
                 official: bool = False,
                 userManagementSupported: bool = False,
                 configuration: UrlDisplayThemeConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.userManagementSupported = userManagementSupported
        self.configuration = configuration or UrlDisplayThemeConfiguration()


theme_descriptor = DeviceDescriptor(configuration_factory=UrlDisplayTheme)
