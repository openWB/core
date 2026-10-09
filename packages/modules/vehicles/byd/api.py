#!/usr/bin/env python3
"""BYD-Cloud-API-Client für openWB.

Protokoll (Login, Envelope-Aufbau, Feldnamen) reverse-engineered von
https://github.com/jkaberg/pyBYD (MIT) und https://github.com/TA2k/ioBroker.byd,
hier synchron mit `requests` statt `aiohttp`/`asyncio` nachgebaut, damit es unter
dem in openWB verwendeten Python 3.9 läuft (pyBYD selbst braucht Python 3.11+,
technisch aber nur wegen der genutzten Bibliotheken, nicht wegen des Protokolls).

Ablauf pro Zyklus (fetch_soc):
  1. Falls noch keine oder eine abgelaufene Session für dieses Fahrzeug im
     Prozess-Cache liegt: Login (Passwort-basiert, AES-verschlüsseltes Payload).
  2. vehicleRealTimeRequest (Trigger) -> vehicleRealTimeResult (Poll, mit Sleep-
     Intervall), bis SoC-Daten vorliegen oder die Versuche aufgebraucht sind.
  3. Bei Session-Fehlercode: einmalig neu einloggen und den Request wiederholen.

Die Session (userId/signToken/encryToken) wird pro (username, vin) im Prozess
zwischengespeichert, damit nicht bei jedem openWB-Zyklus neu eingeloggt wird
(das würde unnötig Bangcle-Berechnungen kosten und die BYD-Cloud unnötig
belasten).
"""
import json
import logging
import secrets
import time
from typing import Any, Dict, List, Optional

from modules.common import req
from modules.common.component_state import CarState
from modules.vehicles.byd import crypto, device_fingerprint
from modules.vehicles.byd.config import BydConfiguration

log = logging.getLogger(__name__)

BASE_URL = "https://dilinkappoversea-eu.byd.auto"

LOGIN_ENDPOINT = "/app/account/login"
VEHICLE_LIST_ENDPOINT = "/app/account/getAllListByUserId"
REALTIME_TRIGGER_ENDPOINT = "/vehicleInfo/vehicle/vehicleRealTimeRequest"
REALTIME_POLL_ENDPOINT = "/vehicleInfo/vehicle/vehicleRealTimeResult"

SESSION_EXPIRED_CODES = {"1002", "1005", "1010"}
ENDPOINT_NOT_SUPPORTED_CODES = {"1001"}
VEHICLE_UNREACHABLE_CODES = {"6002"}

POLL_ATTEMPTS = 10
POLL_INTERVAL_S = 1.5

_ENERGY_TYPE_CODES = {"ev": "0", "hybrid": "2"}

# Prozess-weiter Session-Cache je Account (Session ist account-, nicht fahrzeugbezogen,
# daher username als Key statt (username, vin) - relevant ua wenn die VIN erst per
# Fahrzeugliste ermittelt wird): {username: {"user_id", "sign_token", "encry_token", "created_at"}}
_session_cache: Dict[str, Dict[str, Any]] = {}
_SESSION_TTL_S = 12 * 3600

# Jeder fehlgeschlagene Login verbraucht einen von wenigen Versuchen, bevor der BYD-Account
# gesperrt wird - Cooldown verhindert, dass jeder Zyklus (alle 5min) den Account weiter verbrennt.
_login_failure_cache: Dict[str, Dict[str, Any]] = {}
_LOGIN_FAILURE_COOLDOWN_S = 3600


class BydApiError(Exception):
    """API hat einen Fehlercode != 0 geliefert."""


class BydAuthenticationError(BydApiError):
    """Login fehlgeschlagen oder Session ungültig."""


def _device(config: BydConfiguration) -> Dict[str, str]:
    """Fallback für Direktaufrufe ohne soc.fetch() (zB Tests): generiert nur im
    Speicher, ohne MQTT-Persistenz."""
    if not config.device_fingerprint:
        fingerprint = device_fingerprint.generate()
        config.device_fingerprint = json.dumps(fingerprint)
        log.debug("BYD: Fingerprint generiert (ungespeichert): %s %s",
                  fingerprint["mobileBrand"], fingerprint["mobileModel"])
    return json.loads(config.device_fingerprint)


def _post_secure(endpoint: str, outer_payload: Dict[str, Any]) -> Dict[str, Any]:
    """Bangcle-verschlüsselt das äußere Envelope, sendet es per POST und
    entschlüsselt die Antwort wieder zu einem Dict."""
    encoded = crypto.bangcle_encode(json.dumps(outer_payload, separators=(",", ":")))
    session = req.get_http_session()
    response = session.post(
        f"{BASE_URL}{endpoint}",
        data=json.dumps({"request": encoded}),
        headers={
            "accept-encoding": "identity",
            "content-type": "application/json; charset=UTF-8",
            "user-agent": "okhttp/4.12.0",
        },
        timeout=15,
    )
    response.raise_for_status()
    body = response.json()
    response_str = body.get("response")
    if not response_str:
        raise BydApiError(f"{endpoint}: Antwort enthält kein 'response'-Feld")

    decoded_text = crypto.bangcle_decode(response_str).decode("utf-8").strip()
    if decoded_text.startswith("F{") or decoded_text.startswith("F["):
        decoded_text = decoded_text[1:]
    return json.loads(decoded_text)


def _login(config: BydConfiguration) -> Dict[str, Any]:
    log.debug("BYD: Login für %s", config.username)
    now_ms = int(time.time() * 1000)
    random_hex = secrets.token_hex(16).upper()
    req_timestamp = str(now_ms)
    device = _device(config)
    imei_md5 = device["imeiMd5"]

    inner = {
        "agreeStatus": "0",
        "agreementType": "[1,2]",
        "appInnerVersion": "323",
        "appVersion": "3.2.3",
        "deviceName": device["mobileBrand"] + device["mobileModel"],
        "deviceType": device["deviceType"],
        "imeiMD5": imei_md5,
        "isAuto": "1",
        "mobileBrand": device["mobileBrand"],
        "mobileModel": device["mobileModel"],
        "networkType": device["networkType"],
        "osType": device["osType"],
        "osVersion": device["osVersion"],
        "random": random_hex,
        "softType": "0",
        "timeStamp": req_timestamp,
        "timeZone": "Europe/Amsterdam",
    }
    encry_data = crypto.aes_encrypt_hex(json.dumps(inner, separators=(",", ":")), crypto.pwd_login_key(config.password))
    password_md5 = crypto.md5_hex(config.password)

    sign_fields = {
        **inner,
        "countryCode": config.country_code,
        "functionType": "pwdLogin",
        "identifier": config.username,
        "identifierType": config.identifier_type,
        "language": "en",
        "reqTimestamp": req_timestamp,
    }
    sign = crypto.sha1_mixed(crypto.build_sign_string(sign_fields, password_md5))

    outer = {
        "countryCode": config.country_code,
        "encryData": encry_data,
        "functionType": "pwdLogin",
        "identifier": config.username,
        "identifierType": config.identifier_type,
        "imeiMD5": imei_md5,
        "isAuto": "1",
        "language": "en",
        "reqTimestamp": req_timestamp,
        "sign": sign,
        "signKey": config.password,
        "ostype": device["ostype"],
        "imei": device["imei"],
        "mac": device["mac"],
        "model": device["model"],
        "sdk": device["sdk"],
        "mod": device["mod"],
        "serviceTime": str(int(time.time() * 1000)),
    }
    outer["checkcode"] = crypto.compute_checkcode(outer)

    response = _post_secure(LOGIN_ENDPOINT, outer)
    if str(response.get("code")) != "0":
        raise BydAuthenticationError(
            f"Login fehlgeschlagen: code={response.get('code')} message={response.get('message')}")

    respond_data = response.get("respondData")
    if not respond_data:
        raise BydAuthenticationError("Login-Antwort enthält kein respondData")

    plaintext = crypto.aes_decrypt_utf8(respond_data, crypto.pwd_login_key(config.password))
    token = (json.loads(plaintext) or {}).get("token") or {}
    if not token.get("userId") or not token.get("signToken") or not token.get("encryToken"):
        raise BydAuthenticationError("Login-Antwort enthält keine vollständigen Token-Felder")

    return {
        "user_id": str(token["userId"]),
        "sign_token": str(token["signToken"]),
        "encry_token": str(token["encryToken"]),
        "created_at": time.monotonic(),
    }


def _get_session(config: BydConfiguration, force_relogin: bool = False) -> Dict[str, Any]:
    cache_key = config.username
    cached = _session_cache.get(cache_key)
    if (not force_relogin and cached is not None
            and (time.monotonic() - cached["created_at"]) < _SESSION_TTL_S):
        return cached

    failure = _login_failure_cache.get(cache_key)
    if failure is not None:
        age_s = time.monotonic() - failure["timestamp"]
        if age_s < _LOGIN_FAILURE_COOLDOWN_S:
            raise BydAuthenticationError(
                f"BYD-Login für {config.username} wird für weitere "
                f"{int(_LOGIN_FAILURE_COOLDOWN_S - age_s)}s nicht erneut versucht (letzter "
                f"Versuch vor {int(age_s)}s fehlgeschlagen mit: {failure['message']}). Account/"
                "Zugangsdaten prüfen, um keine Login-Fehlversuche zu verbrauchen.")

    try:
        session = _login(config)
    except BydAuthenticationError as exc:
        _login_failure_cache[cache_key] = {"timestamp": time.monotonic(), "message": str(exc)}
        raise
    _session_cache[cache_key] = session
    _login_failure_cache.pop(cache_key, None)
    return session


def _post_token_json(endpoint: str, config: BydConfiguration, session: Dict[str, Any],
                     inner: Dict[str, str]) -> Any:
    keys = crypto.session_keys(session["sign_token"], session["encry_token"])
    device = _device(config)
    imei_md5 = device["imeiMd5"]
    req_timestamp = str(int(time.time() * 1000))

    encry_data = crypto.aes_encrypt_hex(json.dumps(inner, separators=(",", ":")), keys["content_key"])
    sign_fields = {
        **inner,
        "countryCode": config.country_code,
        "identifier": session["user_id"],
        "imeiMD5": imei_md5,
        "language": "en",
        "reqTimestamp": req_timestamp,
    }
    sign = crypto.sha1_mixed(crypto.build_sign_string(sign_fields, keys["sign_key"]))

    outer = {
        "countryCode": config.country_code,
        "encryData": encry_data,
        "identifier": session["user_id"],
        "imeiMD5": imei_md5,
        "language": "en",
        "reqTimestamp": req_timestamp,
        "sign": sign,
        "ostype": device["ostype"],
        "imei": device["imei"],
        "mac": device["mac"],
        "model": device["model"],
        "sdk": device["sdk"],
        "mod": device["mod"],
        "serviceTime": str(int(time.time() * 1000)),
    }
    outer["checkcode"] = crypto.compute_checkcode(outer)

    response = _post_secure(endpoint, outer)
    code = str(response.get("code", ""))
    if code != "0":
        if code in SESSION_EXPIRED_CODES:
            raise BydAuthenticationError(f"{endpoint}: Session abgelaufen (code={code})")
        if code in ENDPOINT_NOT_SUPPORTED_CODES:
            raise BydApiError(f"{endpoint}: von diesem Fahrzeug nicht unterstützt (code={code})")
        if code in VEHICLE_UNREACHABLE_CODES:
            raise BydApiError(f"{endpoint}: Fahrzeug nicht erreichbar, z.B. im Tiefschlaf (code={code})")
        raise BydApiError(f"{endpoint} fehlgeschlagen: code={code} message={response.get('message')}")

    respond_data = response.get("respondData")
    if not respond_data:
        return {}
    plaintext = crypto.aes_decrypt_utf8(respond_data, keys["content_key"])
    if not plaintext.strip():
        return {}
    return json.loads(plaintext)


def _inner_base(config: BydConfiguration, request_serial: Optional[str] = None) -> Dict[str, str]:
    device = _device(config)
    inner = {
        "deviceType": device["deviceType"],
        "imeiMD5": device["imeiMd5"],
        "networkType": device["networkType"],
        "random": secrets.token_hex(16).upper(),
        "timeStamp": str(int(time.time() * 1000)),
        "version": "351",
    }
    # vin fehlt zB bei der Fahrzeugliste, dort ist sie ja erst das Ergebnis
    if config.vin:
        inner["vin"] = config.vin
    if request_serial:
        inner["requestSerial"] = request_serial
    return inner


def _fetch_vehicle_list(config: BydConfiguration, session: Dict[str, Any]) -> List[Dict[str, Any]]:
    result = _post_token_json(VEHICLE_LIST_ENDPOINT, config, session, _inner_base(config))
    return result if isinstance(result, list) else []


def _resolve_vin(config: BydConfiguration, session: Dict[str, Any]) -> str:
    """Nutzt die konfigurierte VIN, falls vorhanden - sonst das erste Fahrzeug im Account
    (ausreichend, solange nur ein BYD am Account hängt; bei mehreren muss die VIN wie in
    config.py beschrieben explizit gesetzt werden, um eindeutig zu sein)."""
    if config.vin:
        return config.vin
    vehicles = _fetch_vehicle_list(config, session)
    if not vehicles:
        raise BydApiError("Kein Fahrzeug im BYD-Account gefunden und keine VIN konfiguriert")
    vin = vehicles[0].get("vin")
    if not vin:
        raise BydApiError("Fahrzeugliste enthält keine VIN")
    log.debug("BYD: keine VIN konfiguriert, verwende erstes Fahrzeug im Account: %s", vin)
    return vin


def _is_realtime_ready(data: Dict[str, Any]) -> bool:
    """Trigger-Antwort ist nur eine Platzhalter-Quittung mit zB elecPercent=0 statt
    fehlend, "is not None" greift daher nicht. Kriterium wie pyBYDs is_ready_raw:
    offline nie bereit, sonst zählt ein echter Zeitstempel/Reifendruck/Restreichweite."""
    if not data or data.get("onlineState") == 0:
        return False
    tire_fields = ("leftFrontTirepressure", "rightFrontTirepressure",
                   "leftRearTirepressure", "rightRearTirepressure")
    if any(float(data.get(f) or 0) > 0 for f in tire_fields):
        return True
    if int(data.get("time") or 0) > 0:
        return True
    return float(data.get("enduranceMileage") or 0) > 0


def _fetch_realtime(config: BydConfiguration, session: Dict[str, Any]) -> Dict[str, Any]:
    """Trigger + Poll: löst die Fahrzeug-Abfrage aus und pollt dann bis zu
    POLL_ATTEMPTS mal im Abstand von POLL_INTERVAL_S, bis Daten vorliegen."""
    trigger_inner = _inner_base(config)
    trigger_inner["energyType"] = _ENERGY_TYPE_CODES.get(config.energy_type, "0")
    trigger_inner["tboxVersion"] = "3"
    result = _post_token_json(REALTIME_TRIGGER_ENDPOINT, config, session, trigger_inner)
    request_serial = result.get("requestSerial") if isinstance(result, dict) else None

    if isinstance(result, dict) and _is_realtime_ready(result):
        return result

    for attempt in range(1, POLL_ATTEMPTS + 1):
        time.sleep(POLL_INTERVAL_S)
        poll_inner = _inner_base(config, request_serial=request_serial)
        poll_inner["energyType"] = _ENERGY_TYPE_CODES.get(config.energy_type, "0")
        poll_inner["tboxVersion"] = "3"
        try:
            result = _post_token_json(REALTIME_POLL_ENDPOINT, config, session, poll_inner)
        except BydApiError as exc:
            log.debug("BYD: Poll-Versuch %d/%d fehlgeschlagen: %s", attempt, POLL_ATTEMPTS, exc)
            continue
        if isinstance(result, dict):
            request_serial = result.get("requestSerial") or request_serial
            if _is_realtime_ready(result):
                return result

    raise BydApiError("Keine Realtime-Daten erhalten (Fahrzeug antwortet nicht rechtzeitig, evtl. im Tiefschlaf)")


def extract_soc(data: Dict[str, Any]) -> float:
    value = data.get("elecPercent")
    if value is None or float(value) < 0:
        raise BydApiError("SoC (elecPercent) nicht in der Antwort enthalten")
    return float(value)


def extract_range(data: Dict[str, Any]) -> Optional[float]:
    value = data.get("enduranceMileage")
    if value is None or float(value) < 0:
        return None
    return float(value)


def extract_odometer(data: Dict[str, Any]) -> Optional[float]:
    value = data.get("totalMileage")
    if value is None or float(value) < 0:
        return None
    return float(value)


def fetch_soc(config: BydConfiguration, vehicle: int) -> CarState:
    if not config.username or not config.password:
        raise BydApiError("Benutzername und Passwort müssen konfiguriert sein")

    try:
        session = _get_session(config)
        # falls keine VIN konfiguriert ist: per Fahrzeugliste ermittelt und nur im
        # Speicher gecacht (anders als der Fingerprint nicht dauerhaft gespeichert)
        config.vin = _resolve_vin(config, session)
        try:
            data = _fetch_realtime(config, session)
        except BydAuthenticationError:
            log.info("BYD: Session abgelaufen, neuer Login für Fahrzeug %s", vehicle)
            session = _get_session(config, force_relogin=True)
            data = _fetch_realtime(config, session)
    except BydApiError:
        raise
    except Exception as exc:
        raise BydApiError(f"Unerwarteter Fehler beim Abruf der BYD-Daten: {exc}") from exc

    return CarState(
        soc=extract_soc(data),
        range=extract_range(data),
        odometer=extract_odometer(data),
    )
