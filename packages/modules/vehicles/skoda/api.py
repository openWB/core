#!/usr/bin/env python3
import logging
from typing import Optional

log = logging.getLogger(__name__)

# https://public.api.connect.skoda-auto.cz/docs/myskoda-public-api.yaml
BASE_URI = "https://public.api.connect.skoda-auto.cz/api/v1"
SANDBOX_URI = "https://public.test-api.connect.skoda-auto.cz/api/v1"

# Teile, die wir für SoC/Reichweite/Kilometerstand benötigen
INCLUDE_PARTS = ("charging", "odometer")

# Zustände, die einer laufenden Ladung entsprechen (analog evcc-Mapping)
CHARGING_STATES = ("CHARGING", "CONSERVING")
PLUGGED_STATES = ("READY_FOR_CHARGING", "CHARGING_INTERRUPTED", "DISCHARGING") + CHARGING_STATES


class MyskodaApiError(Exception):
    """Wird geworfen, wenn ein von der API benötigter Teil (part) fehlt oder ein Request fehlschlägt."""
    pass


def _base_uri(sandbox: bool) -> str:
    return SANDBOX_URI if sandbox else BASE_URI


def fetch_vehicle(api_key: str, vin: str, sandbox: bool = False, include: tuple = INCLUDE_PARTS) -> dict:
    """Ruft den Fahrzeugstatus von der MyŠkoda Public API ab.

    Die API liefert bei nicht verfügbaren Teilen (z.B. Auto offline) keinen Fehler-Status,
    sondern listet den betroffenen Teil stattdessen unter "errors" auf - siehe part_error().
    """
    from modules.common import req  # lokaler Import: api.py bleibt standalone testbar (siehe test_api.py)

    uri = f"{_base_uri(sandbox)}/vehicles/{vin}"
    if include:
        uri += "?include=" + ",".join(include)

    session = req.get_http_session()
    session.headers.update({"X-API-Key": api_key})
    response = session.get(uri, timeout=10)
    response.raise_for_status()
    return response.json()


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


def charge_action(api_key: str, vin: str, start: bool, sandbox: bool = False) -> None:
    """Startet oder stoppt die Ladung. Wird von openWB soc.py aktuell nicht genutzt,
    steht aber für spätere Ladesteuerung über dieses Modul bereit."""
    from modules.common import req

    action = "start" if start else "stop"
    uri = f"{_base_uri(sandbox)}/vehicles/{vin}/charging/{action}"

    session = req.get_http_session()
    session.headers.update({"X-API-Key": api_key})
    response = session.post(uri, timeout=10)
    response.raise_for_status()


def extract_soc(data: dict) -> float:
    status = ((data.get("charging") or {}).get("status")) or {}
    battery = status.get("battery")
    if battery is None or battery.get("stateOfChargeInPercent") is None:
        raise part_error(data, "CHARGING")
    return float(battery["stateOfChargeInPercent"])


def extract_range(data: dict) -> Optional[float]:
    status = ((data.get("charging") or {}).get("status")) or {}
    battery = status.get("battery")
    meters = battery.get("remainingCruisingRangeInMeters") if battery else None
    if meters is None:
        return None
    return meters / 1000  # Meter -> km


def extract_odometer(data: dict) -> Optional[float]:
    odometer = data.get("odometer")
    if odometer is None or odometer.get("mileageInKm") is None:
        return None
    return float(odometer["mileageInKm"])
