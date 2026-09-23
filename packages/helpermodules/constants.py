from enum import Enum
from pathlib import Path


NO_ERROR = "Kein Fehler."

# Sekunden, nach denen ein andauernder Fehlerzustand einer Komponente dazu führt, dass nicht mehr mit deren
# letztem bekannten Wert weitergerechnet bzw. weiter gesteuert wird (Counter, Chargepoint, PV, Bat, Consumer).
COMPONENT_ERROR_DURATION = 60

RAMDISK_PATH = Path(__file__).resolve().parents[2] / "ramdisk"


class DEFAULT_COLORS(Enum):
    CHARGEPOINT = "#007bff"
    CONSUMER = "#9C65FF"
    VEHICLE = "#17a2b8"
    INVERTER = "#28a745"
    COUNTER = "#dc3545"
    BATTERY = "#ffc107"
    UNKNOWN = "#000000"
