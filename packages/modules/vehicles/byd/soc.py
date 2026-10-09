import json
import logging

from dataclass_utils import asdict
from helpermodules.pub import Pub
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.byd import api, device_fingerprint
from modules.vehicles.byd.config import Byd

log = logging.getLogger(__name__)


def fetch(vehicle_config: Byd, vehicle: int) -> CarState:
    config = vehicle_config.configuration

    # Fingerprint wird einmalig generiert und dauerhaft zurückgeschrieben, damit der Account
    # immer als dasselbe Gerät auftritt statt bei jedem Login neu (siehe device_fingerprint.py)
    if not config.device_fingerprint:
        fingerprint = device_fingerprint.generate()
        config.device_fingerprint = json.dumps(fingerprint)
        log.info("BYD: neuer Geräte-Fingerprint für Fahrzeug %s generiert: %s %s (IMEI %s)",
                 vehicle, fingerprint["mobileBrand"], fingerprint["mobileModel"], fingerprint["imei"])
        Pub().pub(f"openWB/set/vehicle/{vehicle}/soc_module/config", asdict(vehicle_config))

    return api.fetch_soc(config, vehicle)


def create_vehicle(vehicle_config: Byd, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return fetch(vehicle_config, vehicle)

    return ConfigurableVehicle(vehicle_config=vehicle_config,
                               component_updater=updater,
                               vehicle=vehicle,
                               # SoC während der Ladung über die Cloud-API abrufbar,
                               # daher keine manuelle Berechnung nötig
                               calc_while_charging=False)


device_descriptor = DeviceDescriptor(configuration_factory=Byd)
