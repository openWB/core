from helpermodules.auto_str import auto_str

from modules.common.abstract_device import DeviceDescriptor


@auto_str
class KoalaWebThemeConfiguration:
    def __init__(self,
                 hide_standard_vehicle: bool = False,
                 history_chart_range: int = 3600,
                 chargePoint_card_view_breakpoint: int = 4,
                 vehicle_card_view_breakpoint: int = 4,
                 chargePoint_table_search_input_field: bool = False,
                 vehicle_table_search_input_field: bool = False,
                 top_carousel_slide_order: list = None
                 ) -> None:
        self.hide_standard_vehicle = hide_standard_vehicle
        self.history_chart_range = history_chart_range
        self.chargePoint_card_view_breakpoint = chargePoint_card_view_breakpoint
        self.vehicle_card_view_breakpoint = vehicle_card_view_breakpoint
        self.chargePoint_table_search_input_field = chargePoint_table_search_input_field
        self.vehicle_table_search_input_field = vehicle_table_search_input_field
        self.top_carousel_slide_order = top_carousel_slide_order or [
            "flow_diagram",
            "history_chart",
            "daily_totals",
        ]


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
