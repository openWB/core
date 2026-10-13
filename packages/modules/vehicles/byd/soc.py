import json
import logging

from dataclass_utils import asdict
from helpermodules.pub import Pub
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.byd import api
from modules.vehicles.byd.config import Byd

log = logging.getLogger(__name__)


def fetch(vehicle_config: Byd, vehicle: int) -> CarState:
    config = vehicle_config.configuration

    # Fingerprint ist account-, nicht fahrzeugbezogen - dauerhaft in der Fahrzeug-Config gespeichert
    shared_fingerprint = api.resolve_account_fingerprint(config.username, config.device_fingerprint)
    if config.device_fingerprint != shared_fingerprint:
        is_new = not config.device_fingerprint
        config.device_fingerprint = shared_fingerprint
        if is_new:
            fingerprint = json.loads(shared_fingerprint)
            log.info("BYD: neuer Geräte-Fingerprint für Account %s generiert: %s %s (IMEI %s)",
                     config.username, fingerprint["mobileBrand"], fingerprint["mobileModel"],
                     fingerprint["imei"])
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
