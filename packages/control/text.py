import datetime
from enum import Enum


class BidiState(Enum):
    BIDI_CAPABLE = ""
    CP_NOT_BIDI_CAPABLE = "Bidirektionales Laden ist nur mit einer openWB Pro oder Pro+ möglich. "
    CP_WRONG_PROTOCOL = "Bitte in den Einstellungen der openWB Pro/Pro+ die Charging Version auf 'HLC' stellen. "
    EV_NOT_BIDI_CAPABLE = "Das Fahrzeug unterstützt kein bidirektionales Laden. "


def format_next_time_charging_start(next_start: datetime.datetime) -> str:
    today = datetime.datetime.today().date()
    if next_start.date() == today:
        return f"Nächster Zeitladen-Plan startet heute um {next_start.strftime('%-H:%M')} Uhr."
    if next_start.date() == today + datetime.timedelta(days=1):
        return f"Nächster Zeitladen-Plan startet morgen um {next_start.strftime('%-H:%M')} Uhr."
    return f"Nächster Zeitladen-Plan startet am {next_start.strftime('%d.%m.')} um {next_start.strftime('%-H:%M')} Uhr."
