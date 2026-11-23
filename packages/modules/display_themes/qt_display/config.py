import os
from typing import Optional

from helpermodules.auto_str import auto_str
from modules.common.abstract_device import DeviceDescriptor


@auto_str
class QtDisplayThemeConfiguration:
    # TODO: Implement native display theme configuration options
    def __init__(self,
                #  lock_changes: bool = False,
                #  lock_changes_code: Optional[str] = None
                 ) -> None:
        # display lock settings
        # self.lock_changes = lock_changes
        # self.lock_changes_code = lock_changes_code
        pass


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
