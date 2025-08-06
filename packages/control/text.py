from enum import Enum


class BidiState(Enum):
    BIDI_CAPABLE = ""
    CP_NOT_BIDI_CAPABLE = "Bidirektionales Laden ist nur mit einer openWB Pro oder Pro+ möglich. "
    CP_WRONG_PROTOCOL = "Bitte in den Einstellungen der openWB Pro/Pro+ die Charging Version auf 'Bidi' stellen. "
    EV_NOT_BIDI_CAPABLE = "Das Fahrzeug unterstützt kein bidirektionales Laden. "
