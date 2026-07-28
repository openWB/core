import logging

from typing import List, Optional

from helpermodules.cli import run_using_positional_cli_args
from modules.common import req
from modules.common import store
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.iobroker.config import IoBrokerSocSetup, IoBrokerSocConfiguration

log = logging.getLogger(__name__)


def _get_state(base_url: str, state_id: str, timeout: int) -> dict:
    url = f"{base_url}/get/{state_id}"
    response = req.get_http_session().get(url, timeout=timeout)
    return response.json()


def fetch_soc(config: IoBrokerSocSetup) -> CarState:
    cfg = config.configuration
    if cfg.url is None or cfg.url == "":
        raise ValueError("Keine ioBroker-URL definiert. Bitte Konfiguration anpassen.")
    if cfg.state_soc is None or cfg.state_soc == "":
        raise ValueError("Keine State-ID für SoC definiert. Bitte Konfiguration anpassen.")

    soc_state = _get_state(cfg.url, cfg.state_soc, cfg.timeout)
    soc = float(soc_state['val'])
    soc_timestamp = int(soc_state['ts'] / 1000) if soc_state.get('ts') else None

    if cfg.state_range is None or cfg.state_range == "":
        range = None
    else:
        range = float(_get_state(cfg.url, cfg.state_range, cfg.timeout)['val'])

    if cfg.state_odometer is None or cfg.state_odometer == "":
        odometer = None
    else:
        odometer = float(_get_state(cfg.url, cfg.state_odometer, cfg.timeout)['val'])

    return CarState(soc=soc, range=range, odometer=odometer, soc_timestamp=soc_timestamp)


def create_vehicle(vehicle_config: IoBrokerSocSetup, vehicle: int):
    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        return fetch_soc(vehicle_config)
    return ConfigurableVehicle(vehicle_config=vehicle_config,
                               component_updater=updater,
                               vehicle=vehicle,
                               calc_while_charging=vehicle_config.configuration.calculate_soc)


def json_update(charge_point: int, url: str, state_soc: str, state_range: str, state_odometer: str):
    log.debug(f'iobroker-soc: charge_point={charge_point} url="{url}" state_soc="{state_soc}" '
              f'state_range="{state_range}" state_odometer="{state_odometer}"')
    store.get_car_value_store(charge_point).store.set(
        fetch_soc(IoBrokerSocSetup(configuration=IoBrokerSocConfiguration(url=url,
                                                                          state_soc=state_soc,
                                                                          state_range=state_range,
                                                                          state_odometer=state_odometer))))


def main(argv: List[str]):
    run_using_positional_cli_args(json_update, argv)


device_descriptor = DeviceDescriptor(configuration_factory=IoBrokerSocSetup)
