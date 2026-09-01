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
    url = config.configuration.url
    entity_soc = config.configuration.entity_soc
    entity_range = config.configuration.entity_range
    entity_odometer = config.configuration.entity_odometer
    token = config.configuration.token
    if url is None or url == "":
        raise ValueError("Keine URL zum Abrufen der Daten definiert. Bitte Konfiguration anpassen.")
    if token is None or token == "":
        raise ValueError("Kein Token definiert. Bitte Konfiguration anpassen.")
    if entity_soc is None or entity_soc == "":
        raise ValueError("Keine Entitäts-ID für SoC definiert. Bitte Konfiguration anpassen.")
    url_soc = url + "/api/states/" + entity_soc
    response = req.get_http_session().get(url_soc, timeout=10,
                                          headers={
                                              "authorization": "Bearer " + token,
                                              "content-type": "application/json"}
                                          )
    json = response.json()
    soc = float(json['state'])
    soc_timestamp = extract_to_epoch(json['last_changed'])
    if entity_range is None or entity_range == "":
        range = None
    else:
        url_range = url + "/api/states/" + entity_range
        response = req.get_http_session().get(url_range, timeout=10,
                                              headers={
                                                  "authorization": "Bearer " + token,
                                                  "content-type": "application/json"}
                                              )
        json = response.json()
        range = float(json['state'])
    if entity_odometer is None or entity_odometer == "":
        odometer = None
    else:
        url_odometer = url + "/api/states/" + entity_odometer
        response = req.get_http_session().get(url_odometer, timeout=10,
                                              headers={
                                                  "authorization": "Bearer " + token,
                                                  "content-type": "application/json"}
                                              )
        json = response.json()
        odometer = float(json['state'])
    return CarState(soc=soc, range=range, odometer=odometer, soc_timestamp=soc_timestamp)


def create_vehicle(vehicle_config: HaVehicleSocSetup, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return fetch_soc(vehicle_config)
    return ConfigurableVehicle(vehicle_config=vehicle_config,
                               component_updater=updater,
                               vehicle=vehicle,
                               calc_while_charging=vehicle_config.configuration.calculate_soc)


def json_update(charge_point: int,
                url: str,
                token: str,
                entity_soc: str,
                entity_range: str,
                entity_odometer: str
                ):
    log.debug(f'homeassistant-soc: charge_point={charge_point} url="{url}" token="{token}" '
              f'entity_soc="{entity_soc}"'
              f'entity_range="{entity_range}"'
              f'entity_odometer="{entity_odometer}"')
    store.get_car_value_store(charge_point).store.set(
        fetch_soc(HaVehicleSocSetup(configuration=HaVehicleSocConfiguration(url=url,
                                                                            token=token,
                                                                            entity_soc=entity_soc,
                                                                            entity_range=entity_range,
                                                                            entity_odometer=entity_odometer))))


def main(argv: List[str]):
    run_using_positional_cli_args(json_update, argv)


device_descriptor = DeviceDescriptor(configuration_factory=HaVehicleSocSetup)
