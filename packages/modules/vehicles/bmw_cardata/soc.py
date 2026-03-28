import json
import logging
import os
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import List

from helpermodules.cli import run_using_positional_cli_args
from modules.common import store
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.bmw_cardata.config import BmwCardataSetup, BmwCardataConfiguration

log = logging.getLogger(__name__)

BMW_AUTH_URL = "https://customer.bmwgroup.com/gcdm/oauth"
BMW_API_URL = "https://api-cardata.bmwgroup.com"
TOKEN_FILE = "/var/www/html/openWB/data/bmw_cardata_tokens.json"

FIELD_SOC = "vehicle.drivetrain.electricEngine.charging.level"
FIELD_SOC_ALT = "vehicle.drivetrain.batteryManagement.header"
FIELD_RANGE = "vehicle.drivetrain.electricEngine.remainingElectricRange"
FIELD_STATUS = "vehicle.drivetrain.electricEngine.charging.status"

DEFAULT_CONTAINER_NAME = "ChargeStats"
DEFAULT_CONTAINER_PURPOSE = "openWB"
DEFAULT_CONTAINER_DESCRIPTORS = [
    "vehicle.drivetrain.electricEngine.charging.status",
    "vehicle.drivetrain.batteryManagement.header",
    "vehicle.drivetrain.electricEngine.remainingElectricRange",
]


def http_post(url: str, data: dict) -> dict:
    encoded = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=encoded, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="ignore")
        raise Exception(f"BMW CarData HTTP-POST Fehler {e.code}: {body[:300]}")


def http_post_json(url: str, token: str, payload: dict) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
    )
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")
    req.add_header("Content-Type", "application/json")
    req.add_header("x-version", "v1")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="ignore")
        raise Exception(f"BMW CarData HTTP-POST JSON Fehler {e.code}: {body[:300]}")


def http_get(url: str, token: str) -> dict:
    req = urllib.request.Request(url, method="GET")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")
    req.add_header("x-version", "v1")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="ignore")
        if e.code == 403 and "CU-429" in body:
            raise Exception("BMW CarData: Tageslimit erreicht (CU-429).")
        raise Exception(f"BMW CarData HTTP-GET Fehler {e.code}: {body[:300]}")


def save_tokens(tokens: dict, container_id: str = None):
    existing = load_tokens() or {}
    data = {
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
        "id_token": tokens.get("id_token"),
        "expires_at": time.time() + tokens.get("expires_in", 3600) - 60,
        "container_id": container_id if container_id is not None else existing.get("container_id"),
    }
    with open(TOKEN_FILE, "w") as f:
        json.dump(data, f, indent=2)
    os.chmod(TOKEN_FILE, 0o600)
    log.debug("BMW CarData: Tokens gespeichert: %s", TOKEN_FILE)


def load_tokens() -> dict:
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE) as f:
        return json.load(f)


def update_container_id(container_id: str):
    tokens = load_tokens() or {}
    tokens["container_id"] = container_id
    with open(TOKEN_FILE, "w") as f:
        json.dump(tokens, f, indent=2)
    os.chmod(TOKEN_FILE, 0o600)
    log.info("BMW CarData: Container-ID gespeichert: %s", container_id)


def clear_container_id():
    tokens = load_tokens() or {}
    if "container_id" in tokens:
        tokens.pop("container_id", None)
        with open(TOKEN_FILE, "w") as f:
            json.dump(tokens, f, indent=2)
        os.chmod(TOKEN_FILE, 0o600)
        log.warning("BMW CarData: Gespeicherte Container-ID verworfen.")


def get_valid_token(client_id: str) -> str:
    tokens = load_tokens()
    if not tokens:
        raise Exception("BMW CarData: Keine Tokens gefunden. Bitte einmalig auth.py ausführen.")

    if time.time() < tokens.get("expires_at", 0):
        return tokens["access_token"]

    log.info("BMW CarData: Token abgelaufen, führe Refresh durch...")
    try:
        new = http_post(
            f"{BMW_AUTH_URL}/token",
            {
                "grant_type": "refresh_token",
                "refresh_token": tokens["refresh_token"],
                "client_id": client_id,
            },
        )
        save_tokens(new)
        log.info("BMW CarData: Token-Refresh erfolgreich.")
        return new["access_token"]
    except Exception as e:
        raise Exception(
            f"BMW CarData: Token-Refresh fehlgeschlagen: {e}. Bitte auth.py erneut ausführen."
        )


def list_containers(token: str) -> list:
    raw = http_get(f"{BMW_API_URL}/customers/containers", token)
    return raw if isinstance(raw, list) else raw.get("containers", [])


def create_container(token: str) -> str:
    body = {
        "name": DEFAULT_CONTAINER_NAME,
        "purpose": DEFAULT_CONTAINER_PURPOSE,
        "technicalDescriptors": DEFAULT_CONTAINER_DESCRIPTORS,
    }
    log.info("BMW CarData: Erstelle Container automatisch...")
    result = http_post_json(f"{BMW_API_URL}/customers/containers", token, body)
    cid = result.get("containerId") or result.get("id")
    if not cid:
        raise Exception(f"BMW CarData: Container konnte nicht erstellt werden: {result}")
    log.info("BMW CarData: Container erstellt: %s", cid)
    return cid


def get_container_id(token: str, allow_create: bool = True, force_refresh: bool = False) -> str:
    tokens = load_tokens() or {}

    if not force_refresh:
        cid = tokens.get("container_id")
        if cid:
            log.debug("BMW CarData: Container-ID aus Datei: %s", cid)
            return cid

    log.info("BMW CarData: Ermittle Container-ID via API...")
    containers = list_containers(token)
    active = [c for c in containers if c.get("state") == "ACTIVE"]

    if active:
        cid = active[0].get("containerId") or active[0].get("id")
        if not cid:
            raise Exception("BMW CarData: Aktiver Container gefunden, aber ohne containerId.")
        update_container_id(cid)
        return cid

    if not allow_create:
        raise Exception("BMW CarData: Keine aktiven Container gefunden!")

    log.warning("BMW CarData: Keine aktiven Container gefunden. Versuche Auto-Create...")
    cid = create_container(token)
    update_container_id(cid)
    return cid


def fetch_telematic_data(token: str, vin: str, container_id: str) -> dict:
    url = f"{BMW_API_URL}/customers/vehicles/{vin}/telematicData?containerId={container_id}"
    log.debug("BMW CarData: GET %s", url)
    return http_get(url, token)


def fetch_soc(config: BmwCardataSetup) -> CarState:
    cfg = config.configuration

    if cfg.test_mode:
        log.info(
            "BMW CarData: TEST-MODUS – SoC=%s%%, Reichweite=%s km",
            cfg.test_soc,
            cfg.test_range,
        )
        return CarState(soc=cfg.test_soc, range=cfg.test_range)

    if not cfg.client_id:
        raise Exception("BMW CarData: client_id nicht konfiguriert!")
    if not cfg.vin:
        raise Exception("BMW CarData: VIN nicht konfiguriert!")

    token = get_valid_token(cfg.client_id)
    cid = get_container_id(token)

    try:
        raw = fetch_telematic_data(token, cfg.vin, cid)
    except Exception as e:
        msg = str(e)
        if "HTTP-GET Fehler 404" in msg or "HTTP-GET Fehler 400" in msg:
            log.warning("BMW CarData: Gespeicherter Container scheint ungültig. Versuche Neuermittlung...")
            clear_container_id()
            cid = get_container_id(token, allow_create=True, force_refresh=True)
            raw = fetch_telematic_data(token, cfg.vin, cid)
        else:
            raise

    td = raw.get("telematicData", raw)

    def val(key):
        entry = td.get(key, {})
        return entry.get("value") if isinstance(entry, dict) else None

    soc_raw = val(FIELD_SOC) or val(FIELD_SOC_ALT)
    rng_raw = val(FIELD_RANGE)
    status = val(FIELD_STATUS)

    soc = int(float(soc_raw)) if soc_raw is not None else None
    rng = int(float(rng_raw)) if rng_raw is not None else None

    if soc is None:
        raise Exception("BMW CarData: Kein SoC-Wert in API-Antwort gefunden!")

    log.info("BMW CarData: SoC=%s%%, Reichweite=%s km, Status=%s", soc, rng, status)
    return CarState(soc=soc, range=rng)


def create_vehicle(vehicle_config: BmwCardataSetup, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return fetch_soc(vehicle_config)

    return ConfigurableVehicle(
        vehicle_config=vehicle_config,
        component_updater=updater,
        vehicle=vehicle,
        calc_while_charging=vehicle_config.configuration.calculate_soc,
    )


def bmw_cardata_update(client_id: str, vin: str, charge_point: int):
    store.get_car_value_store(charge_point).store.set(
        fetch_soc(
            BmwCardataSetup(
                configuration=BmwCardataConfiguration(
                    client_id=client_id,
                    vin=vin,
                    test_mode=False,
                )
            )
        )
    )


def main(argv: List[str]):
    run_using_positional_cli_args(bmw_cardata_update, argv)


device_descriptor = DeviceDescriptor(configuration_factory=BmwCardataSetup)