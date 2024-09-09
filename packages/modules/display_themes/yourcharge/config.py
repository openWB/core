from typing import Optional
from helpermodules.auto_str import auto_str

from modules.common.abstract_device import DeviceDescriptor


@auto_str
class YourChargeDisplayThemeConfiguration:
    def __init__(self,
                 lock_changes: bool = False,
                 lock_changes_code: Optional[str] = None
                 ) -> None:
        self.lock_changes = lock_changes
        self.lock_changes_code = lock_changes_code


@auto_str
class YourChargeDisplayTheme:
    def __init__(self,
                 name: str = "YourCharge",
                 type: str = "yourcharge",
                 official: bool = False,
                 configuration: YourChargeDisplayThemeConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or YourChargeDisplayThemeConfiguration()


theme_descriptor = DeviceDescriptor(configuration_factory=YourChargeDisplayTheme)
