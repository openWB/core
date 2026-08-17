import logging
import time
from typing import List, Optional

from requests.exceptions import RequestException

from control import data as control_data
from dataclass_utils import asdict
from helpermodules.pub import Pub
from modules.common import req
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.bmw_cardata.config import BmwCardataSetup, BmwCardataConfiguration

log = logging.getLogger(__name__)

BMW_AUTH_URL = "https://customer.bmwgroup.com/gcdm/oauth"
BMW_API_URL = "https://api-cardata.bmwgroup.com"

# Reihenfolge = Priorität beim Auslesen (siehe _extract_first_value): das
# erste Attribut, das in der API-Antwort einen Wert liefert, gewinnt. Alte,
# etablierte Attribute stehen vorne (funktionieren bei den meisten Fahrzeugen
# nach wie vor), neue Fallback-Attribute werden hinten angehängt und greifen
# nur, wenn die vorherigen für das Fahrzeug nicht existieren. Bestehende
# Einträge nicht entfernen – sonst brechen Fahrzeuge, die sie noch liefern.
# Alle Einträge gegen den offiziellen BMW CarData Telematikdatenkatalog
# verifiziert. S. https://github.com/openWB/core/discussions/3420
FIELD_SOC_CANDIDATES = [
    "vehicle.drivetrain.electricEngine.charging.level",
    "vehicle.drivetrain.batteryManagement.header",
    "vehicle.powertrain.electric.battery.stateOfCharge.displayed",
    # "Neue Klasse" (NK/NA5, ab 2026, z.B. neuer iX3/i3): weder charging.level
    # noch batteryManagement.header verfügbar; wird nur bei Fahrtende befüllt.
    "vehicle.trip.segment.end.drivetrain.batteryManagement.hvSoc",
]
FIELD_RANGE_CANDIDATES = [
    "vehicle.drivetrain.electricEngine.remainingElectricRange",
    "vehicle.drivetrain.electricEngine.kombiRemainingElectricRange",
]
FIELD_STATUS = "vehicle.drivetrain.electricEngine.charging.status"
FIELD_ODOMETER_CANDIDATES = [
    "vehicle.vehicle.travelledDistance",
    # wird nur bei Fahrtende befüllt ("Mileage after last drive")
    "vehicle.trip.segment.end.travelledDistance",
]

CONTAINER_NAME = "ChargeStats"
CONTAINER_PURPOSE = "openWB"
CONTAINER_DESCRIPTORS = [
    FIELD_STATUS,
    *FIELD_SOC_CANDIDATES,
    *FIELD_RANGE_CANDIDATES,
    *FIELD_ODOMETER_CANDIDATES,
]
# Manche neueren Fahrzeuge kennen das älteste (erste) SoC-Attribut nicht mehr.
# Legt man einen Container mit einem für das Fahrzeug nicht verfügbaren
# Descriptor an, antwortet die BMW-API dabei offenbar teils mit einem
# Serverfehler statt einer sauberen 400er. Als Fallback wird die
# Container-Erstellung ohne dieses eine Attribut wiederholt.
CONTAINER_DESCRIPTORS_FALLBACK = [d for d in CONTAINER_DESCRIPTORS if d != FIELD_SOC_CANDIDATES[0]]


def _get_session(token: Optional[str] = None):
    session = req.get_http_session()
    session.headers.update({
        "Accept": "application/json",
        "x-version": "v1",
    })
    if token:
        session.headers.update({"Authorization": f"Bearer {token}"})
    return session


def _response_text(exc: Exception) -> str:
    response = getattr(exc, "response", None)
    if response is None:
        return str(exc)
    try:
        return response.text or str(exc)
    except Exception:
        return str(exc)


def _extract_http_status(exc: Exception) -> Optional[int]:
    response = getattr(exc, "response", None)
    if response is not None:
        return getattr(response, "status_code", None)
    return None


def _extract_value(td: dict, key: str):
    entry = td.get(key, {})
    return entry.get("value") if isinstance(entry, dict) else None


def _extract_first_value(td: dict, keys: List[str]):
    for key in keys:
        value = _extract_value(td, key)
        if value is not None:
            return value
    return None


def _post_form(url: str, data: dict) -> dict:
    session = _get_session()
    response = session.post(url, data=data)
    return response.json()


def _get_json(url: str, token: str):
    session = _get_session(token)
    response = session.get(url)
    return response.json()


def _post_json(url: str, token: str, payload: dict) -> dict:
    session = _get_session(token)
    response = session.post(url, json=payload)
    return response.json()


# Manche neueren Fahrzeuge (z.B. iX1, manche MINI) kennen den Descriptor
# FIELD_SOC_CANDIDATES[0] (charging.level) im CarData-Portal nicht mehr. Legt
# man einen Container mit einem für das Fahrzeug nicht verfügbaren Descriptor
# an, antwortet die BMW-API dabei offenbar teils mit einem Serverfehler statt
# einer sauberen 400er (s. https://github.com/openWB/core/discussions/3420).
# Als Fallback wird die Container-Erstellung ohne diesen Descriptor wiederholt.
def _create_container(token: str, descriptors: List[str] = None, _is_retry: bool = False) -> str:
    descriptors = descriptors if descriptors is not None else CONTAINER_DESCRIPTORS
    log.warning("BMW CarData: Keine aktiven Container gefunden. Erstelle neuen Container...")
    try:
        result = _post_json(
            f"{BMW_API_URL}/customers/containers",
            token,
            {
                "name": CONTAINER_NAME,
                "purpose": CONTAINER_PURPOSE,
                "technicalDescriptors": descriptors,
            },
        )
    except RequestException as e:
        if not _is_retry:
            log.warning(
                "BMW CarData: Container-Erstellung fehlgeschlagen (%s). Versuche erneut ohne "
                "'%s' (evtl. für dieses Fahrzeug nicht verfügbar).", e, FIELD_SOC_CANDIDATES[0],
            )
            return _create_container(token, CONTAINER_DESCRIPTORS_FALLBACK, _is_retry=True)
        raise Exception(f"BMW CarData: Container konnte nicht erstellt werden: {e}")

    container_id = result.get("containerId") or result.get("id")
    if not container_id:
        raise Exception(f"BMW CarData: Container konnte nicht erstellt werden: {result}")
    log.info("BMW CarData: Container erstellt: %s", container_id)
    return container_id


def _fetch_telematic_data(token: str, vin: str, container_id: str):
    url = f"{BMW_API_URL}/customers/vehicles/{vin}/telematicData?containerId={container_id}"
    log.debug("BMW CarData: GET %s", url)
    return _get_json(url, token)


def get_valid_token(cfg: BmwCardataConfiguration, vehicle: int, config: BmwCardataSetup) -> str:
    if not cfg.access_token:
        raise Exception("BMW CarData: Keine Tokens gefunden. Bitte BMW-Kopplung in der UI durchführen.")

    if time.time() < cfg.expires_at:
        return cfg.access_token

    log.info("BMW CarData: Token abgelaufen, führe Refresh durch...")
    try:
        new = _post_form(
            f"{BMW_AUTH_URL}/token",
            {
                "grant_type": "refresh_token",
                "refresh_token": cfg.refresh_token,
                "client_id": cfg.client_id,
            },
        )
    except RequestException as e:
        raise Exception(
            f"BMW CarData: Token-Refresh fehlgeschlagen: {e}. Bitte BMW-Kopplung erneut durchführen."
        )

    cfg.access_token = new["access_token"]
    cfg.refresh_token = new.get("refresh_token", cfg.refresh_token)
    cfg.expires_at = time.time() + new.get("expires_in", 3600) - 60

    log.info("BMW CarData: Token-Refresh erfolgreich.")

    # Neuen Token zurück in MQTT schreiben – auch für alle anderen BMW CarData
    # Fahrzeuge mit derselben Client ID damit diese nicht invalidiert werden
    try:
        for ev_key, ev in control_data.data.ev_data.items():
            try:
                soc_module = ev.soc_module
                if soc_module is None:
                    continue
                other_config = soc_module.vehicle_config
                if (hasattr(other_config, 'type') and
                        other_config.type == "bmw_cardata" and
                        other_config.configuration.client_id == cfg.client_id):
                    other_config.configuration.access_token = cfg.access_token
                    other_config.configuration.refresh_token = cfg.refresh_token
                    other_config.configuration.expires_at = cfg.expires_at
                    Pub().pub(
                        f"openWB/set/vehicle/{ev.num}/soc_module/config",
                        asdict(other_config)
                    )
                    log.info(
                        "BMW CarData: Token in MQTT aktualisiert für Fahrzeug %s.", ev.num
                    )
            except Exception as e:
                log.warning("BMW CarData: Token-Sync für Fahrzeug %s fehlgeschlagen: %s", ev_key, e)
    except Exception as e:
        log.warning("BMW CarData: Token-Sync fehlgeschlagen: %s", e)

    return cfg.access_token


def get_container_id(cfg: BmwCardataConfiguration, token: str) -> str:
    if cfg.container_id:
        log.debug("BMW CarData: Container-ID aus Konfiguration: %s", cfg.container_id)
        return cfg.container_id

    log.info("BMW CarData: Ermittle Container-ID via API...")
    raw = _get_json(f"{BMW_API_URL}/customers/containers", token)
    containers = raw if isinstance(raw, list) else raw.get("containers", [])

    openwb = [
        c for c in containers
        if c.get("state") == "ACTIVE" and c.get("purpose") == CONTAINER_PURPOSE
    ]
    active = [c for c in containers if c.get("state") == "ACTIVE"]
    preferred = openwb if openwb else active

    if preferred:
        container_id = preferred[0].get("containerId") or preferred[0].get("id")
        log.info("BMW CarData: Container-ID gefunden: %s", container_id)
    else:
        container_id = _create_container(token)

    cfg.container_id = container_id
    return container_id


def fetch_soc(config: BmwCardataSetup, vehicle: int = 0) -> CarState:
    cfg = config.configuration

    if not cfg.client_id:
        raise Exception("BMW CarData: client_id nicht konfiguriert!")
    if not cfg.vin:
        raise Exception("BMW CarData: VIN nicht konfiguriert!")

    token = get_valid_token(cfg, vehicle, config)
    container_id = get_container_id(cfg, token)

    try:
        raw = _fetch_telematic_data(token, cfg.vin, container_id)
    except RequestException as e:
        status_code = _extract_http_status(e)

        if status_code in (400, 404):
            log.warning(
                "BMW CarData: Container %s ungültig (HTTP %s), ermittle neu...",
                container_id,
                status_code,
            )
            cfg.container_id = ""
            container_id = get_container_id(cfg, token)
            raw = _fetch_telematic_data(token, cfg.vin, container_id)
        else:
            if status_code == 403 and "CU-429" in _response_text(e):
                raise Exception("BMW CarData: Tageslimit erreicht (CU-429).")
            raise Exception(f"BMW CarData: API-Fehler beim Abruf der Telematikdaten: {e}")

    td = raw.get("telematicData", raw)

    soc_raw = _extract_first_value(td, FIELD_SOC_CANDIDATES)
    range_raw = _extract_first_value(td, FIELD_RANGE_CANDIDATES)
    status = _extract_value(td, FIELD_STATUS)
    odometer_raw = _extract_first_value(td, FIELD_ODOMETER_CANDIDATES)

    soc = int(float(soc_raw)) if soc_raw is not None else None
    vehicle_range = int(float(range_raw)) if range_raw is not None else None
    odometer = int(float(odometer_raw)) if odometer_raw is not None else None

    if soc is None:
        raise Exception("BMW CarData: Kein SoC-Wert in API-Antwort gefunden!")

    if vehicle_range is None and cfg.container_id:
        log.warning(
            "BMW CarData: Kein Reichweitenwert im Container gefunden – "
            "Container wird neu erstellt um fehlende Datenpunkte zu ergänzen."
        )
        cfg.container_id = ""

    log.info(
        "BMW CarData: SoC=%s%%, Reichweite=%s km, Status=%s, Odometer=%s km",
        soc,
        vehicle_range,
        status,
        odometer,
    )
    return CarState(soc=soc, range=vehicle_range, odometer=odometer)


def create_vehicle(vehicle_config: BmwCardataSetup, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return fetch_soc(vehicle_config, vehicle)

    return ConfigurableVehicle(
        vehicle_config=vehicle_config,
        component_updater=updater,
        vehicle=vehicle,
        calc_while_charging=vehicle_config.configuration.calculate_soc,
    )


device_descriptor = DeviceDescriptor(configuration_factory=BmwCardataSetup)
