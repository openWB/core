from helpermodules.auto_str import auto_str
from modules.common.abstract_device import DeviceDescriptor


@auto_str
class ColorsWebThemeConfiguration:
    def __init__(self,
                 displayMode: str = 'dark',
                 smartHomeColors: str = 'normal',
                 liveGraphDuration: int = 3600,
                 showGrid: bool = False,
                 decimalPlaces: int = 1,
                 showRelativeArcs: bool = False,
                 showInverters: bool = True,
                 showVehicles: bool = False,
                 showCounters: bool = False,
                 showPrices: bool = False,
                 alternativeEnergy: bool = False,
                 showStandardVehicle: bool = False,
                 lowerPriceBound: float = 0.0,
                 upperPriceBound: float = 0.0
                 ) -> None:
        self.displayMode = displayMode
        self.smartHomeColors = smartHomeColors
        self.liveGraphDuration = liveGraphDuration
        self.showGrid = showGrid
        self.decimalPlaces = decimalPlaces
        self.showRelativeArcs = showRelativeArcs
        self.showInverters = showInverters
        self.showVehicles = showVehicles
        self.showCounters = showCounters
        self.showPrices = showPrices
        self.alternativeEnergy = alternativeEnergy
        self.showStandardVehicle = showStandardVehicle
        self.lowerPriceBound = lowerPriceBound
        self.upperPriceBound = upperPriceBound


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
