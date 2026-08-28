#!/usr/bin/env python3
import logging

from dataclass_utils import asdict
from helpermodules.pub import Pub
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle
from modules.vehicles.porsche.api import PorscheConnectApi
from modules.vehicles.porsche.config import PorscheConnect

log = logging.getLogger(__name__)


def create_vehicle(vehicle_config: PorscheConnect, vehicle: int):
    api = None

    def persist_token(token: dict) -> None:
        # Neue/rotierte Tokens zurueck in die Fahrzeug-Config schreiben (MQTT),
        # damit sie einen Neustart ueberleben. Analog zu bmw_cardata.
        cfg = vehicle_config.configuration
        cfg.access_token = token.get("access_token", "") or ""
        cfg.refresh_token = token.get("refresh_token", "") or ""
        cfg.expires_at = token.get("expires_at", 0) or 0
        Pub().pub(f"openWB/set/vehicle/{vehicle}/soc_module/config", asdict(vehicle_config))

    def initializer():
        nonlocal api
        cfg = vehicle_config.configuration
        token = {}
        if cfg.access_token or cfg.refresh_token:
            token = {"access_token": cfg.access_token,
                     "refresh_token": cfg.refresh_token,
                     "expires_at": cfg.expires_at}
        api = PorscheConnectApi(email=cfg.email, vehicle_id=vehicle,
                                token=token, persist_cb=persist_token)

    def updater(vehicle_update_data: VehicleUpdateData) -> CarState:
        soc, range, soc_ts, odometer = api.fetch_soc(vehicle_config.configuration.vin)
        log.debug(f"Porsche SoC={soc}%, range={range}km, ts={soc_ts}, odo={odometer}km")
        try:
            return CarState(soc=soc, range=range, soc_timestamp=soc_ts, odometer=odometer)
        except TypeError:
            # Aeltere openWB-Versionen (< odometer-Support) kennen odometer noch nicht.
            return CarState(soc=soc, range=range, soc_timestamp=soc_ts)

    return ConfigurableVehicle(vehicle_config=vehicle_config,
                               component_updater=updater,
                               vehicle=vehicle,
                               initializer=initializer,
                               calc_while_charging=vehicle_config.configuration.calculate_soc)


device_descriptor = DeviceDescriptor(configuration_factory=PorscheConnect)
