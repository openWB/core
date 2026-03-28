import json
import logging
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

FIELD_SOC = "vehicle.drivetrain.electricEngine.charging.level"
FIELD_SOC_ALT = "vehicle.drivetrain.batteryManagement.header"
FIELD_RANGE = "vehicle.drivetrain.electricEngine.remainingElectricRange"
FIELD_STATUS = "vehicle.drivetrain.electricEngine.charging.status"
FIELD_ODOMETER = "vehicle.vehicle.travelledDistance"

CONTAINER_NAME = "ChargeStats"
CONTAINER_PURPOSE = "openWB"
CONTAINER_DESCRIPTORS = [
    "vehicle.drivetrain.electricEngine.charging.status",
    "vehicle.drivetrain.electricEngine.charging.level",
    "vehicle.drivetrain.batteryManagement.header",
    "vehicle.drivetrain.electricEngine.remainingElectricRange",
    "vehicle.vehicle.travelledDistance",
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


def get_valid_token(cfg: BmwCardataConfiguration) -> str:
    if not cfg.access_token:
        raise Exception("BMW CarData: Keine Tokens gefunden. Bitte BMW-Kopplung in der UI durchführen.")

    if time.time() < cfg.expires_at:
        return cfg.access_token

    log.info("BMW CarData: Token abgelaufen, führe Refresh durch...")
    try:
        new = http_post(
            f"{BMW_AUTH_URL}/token",
            {
                "grant_type": "refresh_token",
                "refresh_token": cfg.refresh_token,
                "client_id": cfg.client_id,
            },
        )
        cfg.access_token = new["access_token"]
        cfg.refresh_token = new.get("refresh_token", cfg.refresh_token)
        cfg.expires_at = time.time() + new.get("expires_in", 3600) - 60
        log.info("BMW CarData: Token-Refresh erfolgreich.")
        return cfg.access_token
    except Exception as e:
        raise Exception(
            f"BMW CarData: Token-Refresh fehlgeschlagen: {e}. Bitte BMW-Kopplung erneut durchführen."
        )


def get_container_id(cfg: BmwCardataConfiguration, token: str) -> str:
    if cfg.container_id:
        log.debug("BMW CarData: Container-ID aus Konfiguration: %s", cfg.container_id)
        return cfg.container_id

    log.info("BMW CarData: Ermittle Container-ID via API...")
    raw = http_get(f"{BMW_API_URL}/customers/containers", token)
    containers = raw if isinstance(raw, list) else raw.get("containers", [])

    openwb = [
        c for c in containers
        if c.get("state") == "ACTIVE" and c.get("purpose") == CONTAINER_PURPOSE
    ]
    active = [c for c in containers if c.get("state") == "ACTIVE"]
    preferred = openwb if openwb else active

    if preferred:
        cid = preferred[0].get("containerId") or preferred[0].get("id")
        log.info("BMW CarData: Container-ID gefunden: %s", cid)
    else:
        log.warning("BMW CarData: Keine aktiven Container gefunden. Erstelle neuen Container...")
        body = {
            "name": CONTAINER_NAME,
            "purpose": CONTAINER_PURPOSE,
            "technicalDescriptors": CONTAINER_DESCRIPTORS,
        }
        result = http_post_json(f"{BMW_API_URL}/customers/containers", token, body)
        cid = result.get("containerId") or result.get("id")
        if not cid:
            raise Exception(f"BMW CarData: Container konnte nicht erstellt werden: {result}")
        log.info("BMW CarData: Container erstellt: %s", cid)

    cfg.container_id = cid
    return cid


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

    token = get_valid_token(cfg)
    cid = get_container_id(cfg, token)

    url = f"{BMW_API_URL}/customers/vehicles/{cfg.vin}/telematicData?containerId={cid}"
    log.debug("BMW CarData: GET %s", url)

    try:
        raw = http_get(url, token)
    except Exception as e:
        msg = str(e)
        if "HTTP-GET Fehler 404" in msg or "HTTP-GET Fehler 400" in msg:
            log.warning("BMW CarData: Container ungültig, ermittle neu...")
            cfg.container_id = ""
            cid = get_container_id(cfg, token)
            raw = http_get(
                f"{BMW_API_URL}/customers/vehicles/{cfg.vin}/telematicData?containerId={cid}",
                token
            )
        else:
            raise

    td = raw.get("telematicData", raw)

    def val(key):
        entry = td.get(key, {})
        return entry.get("value") if isinstance(entry, dict) else None

    soc_raw = val(FIELD_SOC) or val(FIELD_SOC_ALT)
    rng_raw = val(FIELD_RANGE)
    status = val(FIELD_STATUS)
    odo_raw = val(FIELD_ODOMETER)

    soc = int(float(soc_raw)) if soc_raw is not None else None
    rng = int(float(rng_raw)) if rng_raw is not None else None
    odo = int(float(odo_raw)) if odo_raw is not None else None

    if soc is None:
        raise Exception("BMW CarData: Kein SoC-Wert in API-Antwort gefunden!")

    log.info("BMW CarData: SoC=%s%%, Reichweite=%s km, Status=%s, Odometer=%s km",
             soc, rng, status, odo)
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
