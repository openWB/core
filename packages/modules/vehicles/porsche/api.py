"""Synchroner Client fuer die (inoffizielle) Porsche-Connect-API.

Der Login-Flow (Auth0 "Identifier First": E-Mail -> Passwort -> Resume -> Token)
und die Endpunkte sind portiert aus der Community-Bibliothek pyporscheconnectapi
(https://github.com/CJNE/pyporscheconnectapi, Apache-2.0). Dort ist alles async
(httpx); openWB ruft SoC-Module synchron auf, daher hier eine schlanke
requests-Implementierung ohne zusaetzliche Abhaengigkeiten.

WICHTIG: Diese Schnittstelle ist nicht offiziell von Porsche unterstuetzt und kann
sich jederzeit aendern. Ein aktives Porsche-Connect-Abo ist Voraussetzung.
"""
import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

import requests

log = logging.getLogger(__name__)

# --- Endpunkte / Client-Konstanten (aus pyporscheconnectapi/const.py) --------
AUTHORIZATION_SERVER = "identity.porsche.com"
AUTHORIZATION_URL = f"https://{AUTHORIZATION_SERVER}/authorize"
TOKEN_URL = f"https://{AUTHORIZATION_SERVER}/oauth/token"
REDIRECT_URI = "my-porsche-app://auth0/callback"
AUDIENCE = "https://api.porsche.com"
CLIENT_ID = "XhygisuebbrqQ80byOuU5VncxLIm8E6H"
X_CLIENT_ID = "41843fb4-691d-4970-85c7-2673e8ecef40"
API_BASE_URL = "https://api.ppa.porsche.com/app"
USER_AGENT = "openWB-porsche/1.0"
TIMEOUT = 30

SCOPE = ("openid profile email offline_access mbb ssodb badge vin dealers cars "
         "charging manageCharging plugAndCharge climatisation manageClimatisation "
         "pid:user_profile.porscheid:read pid:user_profile.name:read "
         "pid:user_profile.vehicles:read pid:user_profile.emails:read "
         "pid:user_profile.locale:read")

# Nur die Messgroessen, die openWB braucht (schlanke Antwort, weckt das Auto nicht).
MEASUREMENTS = ["BATTERY_LEVEL", "E_RANGE", "RANGE", "MILEAGE", "BATTERY_CHARGING_STATE"]

# Token-Persistenz: repo/data/modules/porsche/  (parents[4] == Repo-Wurzel)
_DATA_PATH = Path(__file__).resolve().parents[4] / "data" / "modules" / "porsche"


class PorscheApiError(Exception):
    """Allgemeiner API-Fehler."""


class PorscheWrongCredentials(PorscheApiError):
    """E-Mail/Passwort wurde von Porsche abgelehnt."""


class PorscheCaptchaRequired(PorscheApiError):
    """Porsche verlangt ein Captcha - kann headless nicht geloest werden.

    Abhilfe: einmal in der 'My Porsche'-App/Website vom selben Netz aus anmelden,
    danach greift der Login meist wieder ohne Captcha.
    """


class PorscheConnectApi:
    def __init__(self, email: str, password: str, vehicle_id: int) -> None:
        if not email or not password:
            raise PorscheApiError("E-Mail und Passwort muessen konfiguriert sein.")
        self.email = email
        self.password = password
        self.vehicle_id = vehicle_id
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, "X-Client-ID": X_CLIENT_ID})
        self._token: Dict = self._load_token()

    # --- Token-Persistenz ----------------------------------------------------
    @property
    def _token_file(self) -> Path:
        return _DATA_PATH / f"token_{self.vehicle_id}.json"

    def _load_token(self) -> Dict:
        try:
            with open(self._token_file, "r") as f:
                return json.load(f)
        except (FileNotFoundError, ValueError):
            return {}

    def _save_token(self) -> None:
        try:
            _DATA_PATH.mkdir(parents=True, exist_ok=True)
            with open(self._token_file, "w") as f:
                json.dump(self._token, f)
        except OSError:
            log.exception("Porsche-Token konnte nicht gespeichert werden (nicht kritisch).")

    def _token_expired(self, leeway: int = 60) -> bool:
        expires_at = self._token.get("expires_at")
        if not expires_at:
            return True
        return (expires_at - leeway) < time.time()

    # --- OAuth2 (Auth0 Identifier-First) -------------------------------------
    def _location_params(self, resp: requests.Response) -> Dict[str, List[str]]:
        if resp.status_code != 302 or "Location" not in resp.headers:
            raise PorscheApiError(
                f"Erwartete 302-Weiterleitung, erhielt {resp.status_code}.")
        return parse_qs(urlparse(resp.headers["Location"]).query)

    def _fetch_authorization_code(self) -> str:
        # 1. /authorize - liefert bei bestehender Session direkt den code,
        #    sonst eine Weiterleitung auf die Login-Seite mit state-Parameter.
        resp = self.session.get(
            AUTHORIZATION_URL,
            params={
                "response_type": "code",
                "client_id": CLIENT_ID,
                "redirect_uri": REDIRECT_URI,
                "audience": AUDIENCE,
                "scope": SCOPE,
                "state": "openwb",
            },
            allow_redirects=False,
            timeout=TIMEOUT,
        )
        params = self._location_params(resp)
        code = params.get("code", [None])[0]
        if code is not None:
            return code

        # 2. Keine Session -> Identifier-First-Login durchlaufen.
        state = params.get("state", [None])[0]
        if state is None:
            raise PorscheApiError("Kein 'state' in der Auth0-Weiterleitung gefunden.")
        resume_path = self._login_with_identifier(state)

        # 3. Auth-Code-Anfrage fortsetzen.
        resp = self.session.get(
            f"https://{AUTHORIZATION_SERVER}{resume_path}",
            allow_redirects=False,
            timeout=TIMEOUT,
        )
        params = self._location_params(resp)
        code = params.get("code", [None])[0]
        if code is None:
            raise PorscheApiError("Kein Authorization-Code nach dem Login erhalten.")
        return code

    def _login_with_identifier(self, state: str) -> str:
        # 2a. E-Mail
        resp = self.session.post(
            f"https://{AUTHORIZATION_SERVER}/u/login/identifier",
            params={"state": state},
            data={
                "state": state,
                "username": self.email,
                "js-available": True,
                "webauthn-available": False,
                "is-brave": False,
                "webauthn-platform-available": False,
                "action": "default",
            },
            allow_redirects=False,
            timeout=TIMEOUT,
        )
        if resp.status_code == 401:
            raise PorscheWrongCredentials("E-Mail wurde abgelehnt.")
        if resp.status_code == 400:
            raise PorscheCaptchaRequired(
                "Porsche verlangt ein Captcha. Bitte einmal in der My-Porsche-App "
                "anmelden und es danach erneut versuchen.")

        # 2b. Passwort
        resp = self.session.post(
            f"https://{AUTHORIZATION_SERVER}/u/login/password",
            params={"state": state},
            data={
                "state": state,
                "username": self.email,
                "password": self.password,
                "action": "default",
            },
            allow_redirects=False,
            timeout=TIMEOUT,
        )
        if resp.status_code == 400:
            raise PorscheWrongCredentials("Passwort wurde abgelehnt.")
        if "Location" not in resp.headers:
            raise PorscheApiError(
                f"Login-Schritt Passwort: unerwarteter Status {resp.status_code}.")
        # Auth0 braucht einen kurzen Moment, bis der Resume-Pfad gueltig ist.
        time.sleep(2.5)
        return resp.headers["Location"]

    def _exchange_code(self, code: str) -> None:
        resp = self.session.post(
            TOKEN_URL,
            data={
                "client_id": CLIENT_ID,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
            },
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        self._store_token_response(resp.json())

    def _refresh(self) -> bool:
        refresh_token = self._token.get("refresh_token")
        if not refresh_token:
            return False
        resp = self.session.post(
            TOKEN_URL,
            data={
                "client_id": CLIENT_ID,
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            },
            timeout=TIMEOUT,
        )
        if resp.status_code == 403:
            log.debug("Porsche-Refresh-Token ungueltig, voller Login noetig.")
            return False
        resp.raise_for_status()
        self._store_token_response(resp.json())
        return True

    def _store_token_response(self, data: Dict) -> None:
        data["expires_at"] = int(time.time()) + int(data.get("expires_in", 0))
        # refresh_token bleibt erhalten, falls die Antwort keinen neuen liefert
        if not data.get("refresh_token") and self._token.get("refresh_token"):
            data["refresh_token"] = self._token["refresh_token"]
        self._token = data
        self._save_token()

    def _ensure_token(self) -> str:
        if not self._token_expired():
            return self._token["access_token"]
        if self._token.get("refresh_token") and self._refresh():
            return self._token["access_token"]
        code = self._fetch_authorization_code()
        self._exchange_code(code)
        return self._token["access_token"]

    # --- Daten-Endpunkte -----------------------------------------------------
    def _api_get(self, path: str) -> Dict:
        resp = self.session.get(
            f"{API_BASE_URL}{path}",
            headers={"Authorization": f"Bearer {self._ensure_token()}"},
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()

    def list_vehicles(self) -> List[Dict]:
        data = self._api_get("/connect/v1/vehicles")
        return data if isinstance(data, list) else data.get("vehicles", [])

    def resolve_vin(self, configured_vin: Optional[str]) -> str:
        if configured_vin:
            return configured_vin.strip().upper()
        vehicles = self.list_vehicles()
        if not vehicles:
            raise PorscheApiError("Keine Fahrzeuge im Porsche-Konto gefunden.")
        if len(vehicles) > 1:
            vins = ", ".join(v.get("vin", "?") for v in vehicles)
            raise PorscheApiError(
                f"Mehrere Fahrzeuge im Konto ({vins}). Bitte VIN in der Konfiguration angeben.")
        return vehicles[0]["vin"]

    def fetch_soc(self, configured_vin: Optional[str]) -> Tuple[float, Optional[float],
                                                                Optional[float], Optional[float]]:
        """Liest den gespeicherten Fahrzeugstatus (weckt das Auto nicht).

        Returns: (soc [%], range [km] | None, soc_timestamp [s] | None, odometer [km] | None)
        """
        vin = self.resolve_vin(configured_vin)
        query = "&".join(f"mf={m}" for m in MEASUREMENTS)
        status = self._api_get(f"/connect/v1/vehicles/{vin}?{query}")

        measurements = {m["key"]: m for m in status.get("measurements", [])
                        if m.get("status", {}).get("isEnabled", True)}

        battery = measurements.get("BATTERY_LEVEL", {}).get("value", {})
        soc = battery.get("percent")
        if soc is None:
            raise PorscheApiError(
                f"Kein BATTERY_LEVEL fuer VIN {vin} erhalten (Fahrzeug ohne Porsche Connect?).")

        range_km = None
        range_meas = measurements.get("E_RANGE", measurements.get("RANGE", {})).get("value", {})
        if isinstance(range_meas, dict):
            range_km = range_meas.get("kilometers") or range_meas.get("value")

        odometer = None
        mileage = measurements.get("MILEAGE", {}).get("value", {})
        if isinstance(mileage, dict):
            odometer = mileage.get("kilometers") or mileage.get("value")

        soc_ts = self._extract_timestamp(measurements.get("BATTERY_LEVEL", {}))

        return float(soc), range_km, soc_ts, odometer

    # --- Kommandos (optional, Komfort) ---------------------------------------
    # HINWEIS: openWB regelt die Ladung ueber die Wallbox. Direct Charging steuert
    # das Auto direkt und ist NICHT in openWBs automatische Lade-Logik eingebunden -
    # es ist ein manuell ausloesbares Zusatzfeature (z. B. via cli.py).
    def _api_post(self, path: str, payload: Dict) -> Dict:
        resp = self.session.post(
            f"{API_BASE_URL}{path}",
            headers={"Authorization": f"Bearer {self._ensure_token()}"},
            json=payload,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    def send_command(self, configured_vin: Optional[str], key: str,
                     payload: Optional[Dict] = None, poll_timeout: int = 60) -> str:
        """Sendet ein Fahrzeug-Kommando und wartet auf das Ergebnis.

        Returns den finalen Ergebnis-Code (z. B. "SUCCESS"). Wirft bei Fehler.
        """
        vin = self.resolve_vin(configured_vin)
        body = {"key": key, "payload": payload or {"spin": None}}
        response = self._api_post(f"/connect/v1/vehicles/{vin}/commands", body)
        status = response.get("status", {})
        status_id = status.get("id")
        result = status.get("result")
        if not (status_id and result == "ACCEPTED"):
            return result or "UNKNOWN"

        deadline = time.time() + poll_timeout
        while time.time() < deadline:
            time.sleep(5)
            poll = self._api_get(f"/connect/v1/vehicles/{vin}/commands/{status_id}")
            result = poll.get("status", {}).get("result")
            if result in ("ERROR", "FAIL", "FAILED"):
                raise PorscheApiError(f"Kommando {key} fehlgeschlagen: {result}")
            if result and result not in ("ACCEPTED", "IN_PROGRESS", "PERFORMING", "UNKNOWN"):
                return result
        raise PorscheApiError(f"Kommando {key}: kein Ergebnis innerhalb {poll_timeout}s.")

    def direct_charge(self, configured_vin: Optional[str], on: bool) -> str:
        """Startet (on=True) oder stoppt (on=False) das sofortige Laden."""
        key = "DIRECT_CHARGING_START" if on else "DIRECT_CHARGING_STOP"
        return self.send_command(configured_vin, key)

    @staticmethod
    def _extract_timestamp(measurement: Dict) -> Optional[float]:
        ts = (measurement.get("status", {}).get("updatedAt")
              or measurement.get("value", {}).get("timestamp"))
        if not ts:
            return None
        if isinstance(ts, (int, float)):
            return float(ts) / 1000 if ts > 1e10 else float(ts)
        # ISO-8601 String -> Unix-Sekunden
        try:
            from datetime import datetime
            return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
        except (ValueError, AttributeError):
            return None
