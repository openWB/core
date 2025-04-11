from helpermodules.auto_str import auto_str

from modules.common.abstract_device import DeviceDescriptor


@auto_str
class KoalaWebThemeConfiguration:
    def __init__(self,
                 history_chart_range: int = 3600,
                 card_view_breakpoint: int = 4,
                 table_search_input_field: bool = False) -> None:
        self.history_chart_range = history_chart_range
        self.card_view_breakpoint = card_view_breakpoint
        self.table_search_input_field = table_search_input_field


@auto_str
class KoalaWebTheme:
    def __init__(self,
                 name: str = "Koala",
                 type: str = "koala",
                 official: bool = True,
                 configuration: KoalaWebThemeConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or KoalaWebThemeConfiguration()


theme_descriptor = DeviceDescriptor(configuration_factory=KoalaWebTheme)
