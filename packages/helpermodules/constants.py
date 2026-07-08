from enum import Enum
from pathlib import Path


NO_ERROR = "Kein Fehler."

RAMDISK_PATH = Path(__file__).resolve().parents[2] / "ramdisk"


class DEFAULT_COLORS(Enum):
    CHARGEPOINT = "#007bff"
    VEHICLE = "#17a2b8"
    INVERTER = "#28a745"
    COUNTER = "#dc3545"
    BATTERY = "#ffc107"
    UNKNOWN = "#000000"
