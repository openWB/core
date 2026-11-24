from typing import Optional

from helpermodules.auto_str import auto_str
from modules.common.abstract_device import DeviceDescriptor


@auto_str
class QtDisplayThemeConfiguration:
    def __init__(self,
                 default_view: str = "dashboard",
                 default_view_timeout: int = 0,
                 enable_dashboard_view: bool = True,
                 enable_energy_flow_view: bool = True,
                 enable_charge_points_view: bool = True,
                 enable_energy_graph_view: bool = True,
                 enable_pv_power_price_view: bool = True,
                 enable_consumers_view: bool = True,
                 enable_batteries_view: bool = True,
                 enable_dashboard_card_battery_sum: bool = True,
                 enable_dashboard_card_charge_point_sum: bool = True,
                 enable_dashboard_card_consumers: bool = True,
                 enable_dashboard_card_grid: bool = True,
                 enable_dashboard_card_home_consumption: bool = True,
                 enable_dashboard_card_inverter_sum: bool = True,
                 lock_changes: bool = False,
                 lock_changes_code: Optional[str] = None,
                 simple_charge_point_view: bool = False
                 ) -> None:
        self.default_view = default_view
        self.default_view_timeout = default_view_timeout
        self.enable_dashboard_view = enable_dashboard_view
        self.enable_energy_flow_view = enable_energy_flow_view
        self.enable_charge_points_view = enable_charge_points_view
        self.enable_energy_graph_view = enable_energy_graph_view
        self.enable_pv_power_price_view = enable_pv_power_price_view
        self.enable_consumers_view = enable_consumers_view
        self.enable_batteries_view = enable_batteries_view
        self.enable_dashboard_card_battery_sum = enable_dashboard_card_battery_sum
        self.enable_dashboard_card_charge_point_sum = enable_dashboard_card_charge_point_sum
        self.enable_dashboard_card_consumers = enable_dashboard_card_consumers
        self.enable_dashboard_card_grid = enable_dashboard_card_grid
        self.enable_dashboard_card_home_consumption = enable_dashboard_card_home_consumption
        self.enable_dashboard_card_inverter_sum = enable_dashboard_card_inverter_sum
        self.lock_changes = lock_changes
        self.lock_changes_code = lock_changes_code
        self.simple_charge_point_view = simple_charge_point_view

@auto_str
class QtDisplayTheme:
    def __init__(self,
                 name: str = "QT Display",
                 type: str = "qt_display",
                 official: bool = True,
                 userManagementSupported: bool = False,
                 configuration: Optional[QtDisplayThemeConfiguration] = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.userManagementSupported = userManagementSupported
        self.configuration = configuration or QtDisplayThemeConfiguration()


theme_descriptor = DeviceDescriptor(configuration_factory=QtDisplayTheme)
