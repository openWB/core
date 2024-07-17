from typing import Optional
from helpermodules.auto_str import auto_str

from modules.common.abstract_device import DeviceDescriptor


@auto_str
class ColorsDisplayThemeConfiguration:
    def __init__(self,
                 lock_changes: bool = False,
                 lock_changes_code: Optional[str] = None
                 ) -> None:
        # display lock settings
        self.lock_changes = lock_changes
        self.lock_changes_code = lock_changes_code


@auto_str
class ColorsDisplayTheme:
    def __init__(self,
                 name: str = "Colors",
                 type: str = "colors",
                 official: bool = False,
                 configuration: ColorsDisplayThemeConfiguration = None) -> None:
        self.name = name
        self.type = type
        self.official = official
        self.configuration = configuration or ColorsDisplayThemeConfiguration()


theme_descriptor = DeviceDescriptor(configuration_factory=ColorsDisplayTheme)
