#!/usr/bin/env python3
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

from modules.common import req

log = logging.getLogger(__name__)

# https://public.api.connect.skoda-auto.cz/docs/myskoda-public-api.yaml
BASE_URI = "https://public.api.connect.skoda-auto.cz/api/v1"

# Teile, die wir für SoC/Reichweite/Kilometerstand benötigen
INCLUDE_PARTS = ("charging", "odometer")

# Header, über den die API das Ablaufdatum des Keys mitteilt (siehe Livetest-Ausgabe)
KEY_EXPIRY_HEADER = "X-API-Key-Expires-At"
KEY_EXPIRY_WARN_DAYS = 14


class MyskodaApiError(Exception):
    """Wird geworfen, wenn ein von der API benötigter Teil (part) fehlt oder ein Request fehlschlägt."""
    pass


def check_key_expiry(response, warn_days: int = KEY_EXPIRY_WARN_DAYS) -> None:
    """Loggt eine Warnung, wenn der API-Key laut Response-Header innerhalb von
    warn_days Tagen abläuft. Bricht den Abruf nicht ab - der SoC-Wert wird trotzdem
    zurückgegeben, es soll nur rechtzeitig auf die nötige Erneuerung in der
    MyŠkoda-App hingewiesen werden.
    """
    expires_at = response.headers.get(KEY_EXPIRY_HEADER)
    if not expires_at:
        return
    try:
        expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    except ValueError:
        log.debug(f"Konnte {KEY_EXPIRY_HEADER}-Header nicht parsen: {expires_at}")
        return
    remaining = expiry - datetime.now(timezone.utc)
    if remaining <= timedelta(days=warn_days):
        log.warning(
            f"MyŠkoda API-Key läuft am {expiry.strftime('%d.%m.%Y')} ab "
            f"(noch {max(remaining.days, 0)} Tage) - bitte rechtzeitig in der MyŠkoda-App erneuern."
        )


def fetch_vehicle(api_key: str, vin: str, include: tuple = INCLUDE_PARTS) -> Tuple[dict, Optional[str]]:
    """Ruft den Fahrzeugstatus von der MyŠkoda Public API ab.

    Die API liefert bei nicht verfügbaren Teilen (z.B. Auto offline) keinen Fehler-Status,
    sondern listet den betroffenen Teil stattdessen unter "errors" auf - siehe part_error().

    Rückgabe: (rohe JSON-Antwort, key_expires_at aus dem Response-Header oder None).
    key_expires_at wird von soc.py in die Fahrzeug-Konfiguration zurückgeschrieben,
    damit die Gültigkeit des Keys auch im UI angezeigt werden kann.
    """
    uri = f"{BASE_URI}/vehicles/{vin}"
    if include:
        uri += "?include=" + ",".join(include)

    session = req.get_http_session()
    session.headers.update({"X-API-Key": api_key})
    response = session.get(uri, timeout=10)
    response.raise_for_status()
    check_key_expiry(response)
    return response.json(), response.headers.get(KEY_EXPIRY_HEADER)


def part_error(data: dict, part_prefix: str) -> MyskodaApiError:
    """Sucht in data["errors"] nach einem Eintrag, dessen type mit part_prefix beginnt
    (z.B. "CHARGING", "ODOMETER"), und gibt dessen Meldung als Exception zurück.
    Fällt auf eine generische Meldung zurück, falls die API dazu nichts mitteilt.
    """
    for error in data.get("errors", []) or []:
        error_type = error.get("type", "")
        if error_type.startswith(part_prefix):
            description = error.get("description", "keine Beschreibung")
            return MyskodaApiError(f"{error_type}: {description}")
    return MyskodaApiError(f"{part_prefix} nicht verfügbar")


def charge_action(api_key: str, vin: str, start: bool) -> None:
    """Startet oder stoppt die Ladung. Wird von openWB soc.py aktuell nicht genutzt,
    steht aber für spätere Ladesteuerung über dieses Modul bereit."""
    action = "start" if start else "stop"
    uri = f"{BASE_URI}/vehicles/{vin}/charging/{action}"

    session = req.get_http_session()
    session.headers.update({"X-API-Key": api_key})
    response = session.post(uri, timeout=10)
    response.raise_for_status()


# Feldnamen bestätigt gegen eine echte API-Antwort (02.09.2026, Enyaq).
def extract_soc(data: dict) -> float:
    vehicle = data.get("vehicle") or {}
    status = ((vehicle.get("charging") or {}).get("status")) or {}
    battery = status.get("battery")
    if battery is None or battery.get("stateOfChargeInPercent") is None:
        raise part_error(data, "CHARGING")
    return float(battery["stateOfChargeInPercent"])


def extract_range(data: dict) -> Optional[float]:
    vehicle = data.get("vehicle") or {}
    status = ((vehicle.get("charging") or {}).get("status")) or {}
    battery = status.get("battery")
    meters = battery.get("remainingCruisingRangeInMeters") if battery else None
    if meters is None:
        return None
    return meters / 1000  # Meter -> km


def extract_odometer(data: dict) -> Optional[float]:
    vehicle = data.get("vehicle") or {}
    odometer = vehicle.get("odometer")
    if odometer is None or odometer.get("mileageInKm") is None:
        return None
    return float(odometer["mileageInKm"])
