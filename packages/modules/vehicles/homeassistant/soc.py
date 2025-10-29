import logging

from typing import List, Union
from datetime import datetime

from helpermodules.cli import run_using_positional_cli_args
from modules.common import req
from modules.common import store
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.homeassistant.config import HaVehicleSocSetup, HaVehicleSocConfiguration


log = logging.getLogger(__name__)


def extract_to_epoch(input_string: Union[str, int, float]) -> float:
    # If already an integer, return it
    if isinstance(input_string, int) or isinstance(input_string, float):
        return int(input_string)

    # Try parsing as UTC formatted time
    try:
        dt = datetime.fromisoformat(input_string)
        return int(dt.timestamp())
    except ValueError:
        log.exception(f'Kein ISO 8601 formatiertes Datum in "{input_string}" gefunden.')
        return None


def fetch_soc(config: HaVehicleSocSetup) -> CarState:
    url = config.configuration.url+"/api/states/"+config.configuration.entity_id
    if url is None or url == "":
        raise ValueError("Keine URL zum Abrufen der Daten definiert. Bitte in der Konfiguration aktualisieren.")
    response = req.get_http_session().get(url, timeout=10,
                                          headers={
                                              "authorization": "Bearer " + config.configuration.token,
                                              "content-type": "application/json"}
                                          )
    response.raise_for_status()
    json = response.json()
    soc = float(json['state'])
    soc_timestamp = extract_to_epoch(json['last_changed'])
    return CarState(soc=soc, soc_timestamp=soc_timestamp)


def create_vehicle(vehicle_config: HaVehicleSocSetup, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return fetch_soc(vehicle_config)
    return ConfigurableVehicle(vehicle_config=vehicle_config,
                               component_updater=updater,
                               vehicle=vehicle)


def json_update(charge_point: int,
                url: str,
                token: str,
                entity_id: str
                ):
    log.debug(f'homeassistant-soc: charge_point={charge_point} url="{url}" token="{token}" '
              f'entity_id="{entity_id}"')
    store.get_car_value_store(charge_point).store.set(
        fetch_soc(HaVehicleSocSetup(configuration=HaVehicleSocConfiguration(url=url,
                                                                            token=token,
                                                                            entity_id=entity_id))))


def main(argv: List[str]):
    run_using_positional_cli_args(json_update, argv)


device_descriptor = DeviceDescriptor(configuration_factory=HaVehicleSocSetup)
