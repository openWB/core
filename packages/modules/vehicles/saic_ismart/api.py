#!/usr/bin/env python3
"""SAIC/MG-iSMART-Cloud-API-Client für openWB.

Protokoll (Login, Request-/Response-Verschlüsselung, Endpunkte) reverse-engineered von
https://github.com/SAIC-iSmart-API/saic-python-client-ng (MIT), hier synchron mit
`requests` statt `httpx`/`asyncio` nachgebaut, damit es unter dem in openWB verwendeten
Python 3.9 läuft (die Referenzbibliothek selbst braucht Python 3.11+, technisch aber nur
wegen der genutzten Bibliotheken, nicht wegen des Protokolls).

Ablauf pro Zyklus (fetch_soc):
  1. Falls noch keine oder eine abgelaufene Session für diesen Account im Prozess-Cache
     liegt: Login (Passwort-basiert).
  2. vehicle/charging/mgmtData abfragen. Manche Endpunkte beantwortet die Cloud nicht
     sofort, sondern verweist per Antwort-Header "event-id" auf einen späteren Abruf
     mit genau dieser ID - wird wiederholt, bis Daten vorliegen oder ein Timeout greift.
  3. Liefert die Cloud nur den Sentinel-Wert (Fahrzeug schläft, Daten noch nicht
     aktuell): vehicle/status abfragen (weckt das Fahrzeug) und mgmtData erneut abfragen.
"""
import json
import logging
import time
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlencode

from modules.common import req
from modules.common.component_state import CarState
from modules.vehicles.saic_ismart import crypto
from modules.vehicles.saic_ismart.config import SaicIsmartConfiguration

log = logging.getLogger(__name__)

BASE_URL = "https://gateway-mg-eu.soimt.com/api.app/v1"
TENANT_ID = "459771"

LOGIN_ENDPOINT = "/oauth/token"
VEHICLE_LIST_ENDPOINT = "/vehicle/list"
VEHICLE_STATUS_ENDPOINT = "/vehicle/status"
CHARGING_MGMT_ENDPOINT = "/vehicle/charging/mgmtData"

# Fehlercodes, die nie retrybar sind (anders als zB ein fehlendes "data" bei Event-ID-Polls)
HARD_ERROR_CODES = (2, 3, 7)

# 10-Bit-Sentinel (0x3FF): die Cloud hat noch keine aktuellen Daten vom Fahrzeug -
# erst per vehicle/status wecken, dann erneut abfragen.
SOC_INVALID_SENTINEL = 1023

EVENT_ID_POLL_TIMEOUT_S = 30
EVENT_ID_POLL_INTERVAL_S = 3

# Prozess-weiter Session-Cache je Account: {username: {"access_token", "expires_at"}}
_session_cache: Dict[str, Dict[str, Any]] = {}
_SESSION_SAFETY_MARGIN_S = 60


class SaicApiError(Exception):
    """API hat einen Fehlercode != 0 geliefert."""


class SaicAuthenticationError(SaicApiError):
    """Login fehlgeschlagen oder Session ungültig (code 401/403)."""


def _send(method: str, path_with_query: str, config: SaicIsmartConfiguration,
          access_token: str, form_body: Optional[Dict[str, str]] = None,
          event_id: Optional[str] = None) -> Tuple[Dict[str, Any], Optional[str]]:
    """Baut die verschlüsselte+signierte Anfrage, sendet sie und entschlüsselt die
    Antwort. Gibt die rohen JSON-Daten sowie einen evtl. vorhandenen
    Retry-Event-ID-Antwort-Header zurück - die Fehlercode-Auswertung macht der Aufrufer."""
    timestamp_ms = str(int(time.time() * 1000))
    content_type = "application/x-www-form-urlencoded" if form_body is not None else "application/json"
    plaintext_body = urlencode(form_body) if form_body is not None else ""
    encrypted_body = crypto.encrypt_request_body(
        path_with_query, TENANT_ID, access_token, timestamp_ms, content_type, plaintext_body)
    headers = crypto.build_signed_headers(
        path_with_query, TENANT_ID, access_token, config.region, content_type,
        encrypted_body, plaintext_body, timestamp_ms)
    if method == "POST" and form_body is not None:
        headers["Authorization"] = "Basic c3dvcmQ6c3dvcmRfc2VjcmV0"
    if event_id is not None:
        headers["event-id"] = event_id

    session = req.get_http_session()
    response = session.request(
        method, f"{BASE_URL}{path_with_query}",
        data=encrypted_body if encrypted_body else None, headers=headers, timeout=15)
    response.raise_for_status()

    body_text = response.text
    resp_ts = response.headers.get("APP-SEND-DATE")
    resp_content_type = response.headers.get("ORIGINAL-CONTENT-TYPE")
    if body_text and resp_ts and resp_content_type:
        body_text = crypto.decrypt_response_body(body_text, resp_ts, resp_content_type)

    data = json.loads(body_text) if body_text else {}
    return data, response.headers.get("event-id")


def _check_code(path: str, data: Dict[str, Any]) -> None:
    code = data.get("code", -1)
    if code in (401, 403):
        raise SaicAuthenticationError(f"{path}: Session abgelaufen (code={code})")
    if code not in (0, None):
        raise SaicApiError(f"{path} fehlgeschlagen: code={code} message={data.get('message')}")


def _request(method: str, path: str, config: SaicIsmartConfiguration, access_token: str,
             form_body: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Einfacher Request ohne Event-ID-Polling (Login, Fahrzeugliste)."""
    data, _ = _send(method, path, config, access_token, form_body)
    _check_code(path, data)
    return data.get("data", {})


def _request_with_event_id_poll(method: str, path: str, config: SaicIsmartConfiguration,
                                access_token: str) -> Dict[str, Any]:
    """Request mit Event-ID-Polling (vehicle/status, vehicle/charging/mgmtData):
    liefert die Cloud noch keine Daten, verweist sie per Antwort-Header "event-id" auf
    einen späteren Abruf - wiederholt mit dieser ID, bis Daten vorliegen oder Timeout."""
    event_id = "0"
    deadline = time.monotonic() + EVENT_ID_POLL_TIMEOUT_S
    while True:
        data, response_event_id = _send(method, path, config, access_token, event_id=event_id)
        code = data.get("code", -1)

        if code in (401, 403):
            raise SaicAuthenticationError(f"{path}: Session abgelaufen (code={code})")
        if code in HARD_ERROR_CODES:
            raise SaicApiError(f"{path} fehlgeschlagen: code={code} message={data.get('message')}")

        if response_event_id and "data" not in data:
            next_event_id = response_event_id
        elif code not in (0, None):
            if event_id == "0":
                raise SaicApiError(f"{path} fehlgeschlagen: code={code} message={data.get('message')}")
            next_event_id = event_id
        else:
            return data.get("data", {})

        if time.monotonic() >= deadline:
            raise SaicApiError(f"{path}: keine Daten erhalten (Fahrzeug antwortet nicht "
                               "rechtzeitig, evtl. im Tiefschlaf)")
        event_id = next_event_id
        time.sleep(EVENT_ID_POLL_INTERVAL_S)


def _login(config: SaicIsmartConfiguration) -> Dict[str, Any]:
    log.debug("SAIC iSMART: Login für %s", config.username)
    form_body = {
        "grant_type": "password",
        "username": config.username,
        "password": crypto.pwd_login_hash(config.password),
        "scope": "all",
        "deviceId": f"openwb{'0' * 41}{int(time.time())}###com.saicmotor.europecar",
        "deviceType": "0",
        "language": "EN",
    }
    if config.username_is_email:
        form_body["loginType"] = "2"
    elif config.phone_country_code:
        form_body["loginType"] = "1"
        form_body["countryCode"] = config.phone_country_code
    else:
        raise SaicApiError("SAIC iSMART: Benutzername ist keine E-Mail, aber keine "
                           "Landesvorwahl für die Telefonnummer konfiguriert")

    data = _request("POST", LOGIN_ENDPOINT, config, "", form_body=form_body)
    access_token = data.get("access_token")
    expires_in = data.get("expires_in")
    if not access_token or not expires_in:
        raise SaicAuthenticationError(
            "SAIC iSMART: Login fehlgeschlagen, keine Zugangsdaten in der Antwort "
            "(Benutzername/Passwort prüfen)")
    return {
        "access_token": access_token,
        "expires_at": time.monotonic() + expires_in - _SESSION_SAFETY_MARGIN_S,
    }


def _get_session(config: SaicIsmartConfiguration, force_relogin: bool = False) -> str:
    cache_key = config.username
    cached = _session_cache.get(cache_key)
    if not force_relogin and cached is not None and time.monotonic() < cached["expires_at"]:
        return cached["access_token"]
    session = _login(config)
    _session_cache[cache_key] = session
    return session["access_token"]


def _resolve_vin(config: SaicIsmartConfiguration, access_token: str) -> str:
    if config.vin:
        return config.vin
    data = _request("GET", VEHICLE_LIST_ENDPOINT, config, access_token)
    vehicles = data.get("vinList", [])
    if not vehicles:
        raise SaicApiError("SAIC iSMART: Kein Fahrzeug im Account gefunden und keine "
                           "VIN konfiguriert")
    for v in vehicles:
        if v.get("isCurrentVehicle"):
            return v["vin"]
    return vehicles[0]["vin"]


def _fetch_charging_mgmt_data(config: SaicIsmartConfiguration, access_token: str,
                              vin: str) -> Dict[str, Any]:
    path = f"{CHARGING_MGMT_ENDPOINT}?{urlencode({'vin': crypto.vin_hash(vin)})}"
    return _request_with_event_id_poll("GET", path, config, access_token)


def _wake_vehicle(config: SaicIsmartConfiguration, access_token: str, vin: str) -> None:
    path = f"{VEHICLE_STATUS_ENDPOINT}?{urlencode({'vin': crypto.vin_hash(vin), 'vehStatusReqType': '2'})}"
    _request_with_event_id_poll("GET", path, config, access_token)


def extract_soc(data: Dict[str, Any]) -> float:
    soc = (data.get("chrgMgmtData") or {}).get("bmsPackSOCDsp")
    if soc is None or soc == SOC_INVALID_SENTINEL:
        raise SaicApiError("SAIC iSMART: Kein gültiger SoC-Wert erhalten")
    return soc / 10


def extract_range(data: Dict[str, Any]) -> Optional[float]:
    value = (data.get("rvsChargeStatus") or {}).get("fuelRangeElec")
    return (value / 10) if value is not None else None


def extract_odometer(data: Dict[str, Any]) -> Optional[float]:
    value = (data.get("rvsChargeStatus") or {}).get("mileage")
    return (value / 10) if value is not None else None


def fetch_soc(config: SaicIsmartConfiguration) -> CarState:
    if not config.username or not config.password:
        raise SaicApiError("SAIC iSMART: Benutzername und Passwort müssen konfiguriert sein")

    try:
        access_token = _get_session(config)
        vin = _resolve_vin(config, access_token)
        try:
            data = _fetch_charging_mgmt_data(config, access_token, vin)
        except SaicAuthenticationError:
            access_token = _get_session(config, force_relogin=True)
            data = _fetch_charging_mgmt_data(config, access_token, vin)

        soc = (data.get("chrgMgmtData") or {}).get("bmsPackSOCDsp")
        if soc is None or soc == SOC_INVALID_SENTINEL:
            log.info("SAIC iSMART: Cloud-Daten veraltet, wecke Fahrzeug...")
            _wake_vehicle(config, access_token, vin)
            data = _fetch_charging_mgmt_data(config, access_token, vin)
    except SaicApiError:
        raise
    except Exception as exc:
        raise SaicApiError(f"Unerwarteter Fehler beim Abruf der SAIC-Daten: {exc}") from exc

    return CarState(
        soc=extract_soc(data),
        range=extract_range(data),
        odometer=extract_odometer(data),
    )
