#!/usr/bin/env python3
from datetime import datetime
import logging
import time
from typing import Optional

from modules.common import req
from modules.vehicles.pleos.config import PleosToken

log = logging.getLogger(__name__)

BASE_URL = "https://api.pleos.ai/v1"

_UNIT_TO_KM = {"km": 1, "mile": 1.609344, "miles": 1.609344, "meter": 0.001, "feet": 0.0003048}


def validate_token(brand: str, client_id: str, client_secret: str, token: PleosToken) -> PleosToken:
    if token.access_token is not None and time.time() < token.created_at + token.expires_in:
        return token
    return _request_token(brand, client_id, client_secret)


def _request_token(brand: str, client_id: str, client_secret: str) -> PleosToken:
    response = req.get_http_session().post(
        BASE_URL + "/auth/personal-token",
        json={"clientId": client_id, "clientSecret": client_secret},
        headers={"Brand": brand},
        timeout=10,
    )
    data = response.json().get("data", {})
    access_token = data.get("accessToken")
    if not access_token:
        raise Exception("Pleos: Token-Antwort enthält keinen accessToken.")
    return PleosToken(access_token=access_token, expires_in=data.get("expiresIn") or 3600,
                      created_at=int(time.time()))


def _auth_headers(brand: str, token: PleosToken) -> dict:
    return {"Brand": brand, "Authorization": "Bearer " + token.access_token}


def get_battery(brand: str, vin: str, token: PleosToken) -> dict:
    response = req.get_http_session().get(
        BASE_URL + f"/vehicles/{vin}/batteries", headers=_auth_headers(brand, token), timeout=10)
    return response.json().get("data", {})


def get_distance_to_empty_km(brand: str, vin: str, token: PleosToken) -> Optional[float]:
    response = req.get_http_session().get(
        BASE_URL + f"/vehicles/{vin}/powertrains", headers=_auth_headers(brand, token), timeout=10)
    for entry in response.json().get("data", {}).get("distanceToEmpties", []):
        if entry.get("type") == "EV":
            return _to_km(entry.get("value"), entry.get("unit"))
    return None


def get_odometer_km(brand: str, vin: str, token: PleosToken) -> Optional[float]:
    response = req.get_http_session().get(
        BASE_URL + f"/vehicles/{vin}/driving", headers=_auth_headers(brand, token), timeout=10)
    odometer = response.json().get("data", {}).get("odometer", {})
    return _to_km(odometer.get("value"), odometer.get("unit"))


def _to_km(value, unit: str) -> Optional[float]:
    try:
        value = float(value)
    except (TypeError, ValueError):
        return None
    return value * _UNIT_TO_KM.get(unit or "km", 1)


def parse_timestamp(value: Optional[str]) -> Optional[float]:
    # Pleos liefert idR den letzten vom Fahrzeug gemeldeten Stand, nicht live -
    # ohne diesen Zeitstempel würde CarState "jetzt" annehmen und die
    # Veraltungs-/Reihenfolge-Prüfung in ConfigurableVehicle wirkungslos machen.
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None
