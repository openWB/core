#!/usr/bin/env python3
import logging

from modules.common import req
from modules.vehicles.tronity.config import TronityVehicleSocConfiguration
from modules.common.abstract_soc import SocUpdateData
from modules.common.component_state import CarState

log = logging.getLogger(__name__)


def fetch_soc(config: TronityVehicleSocConfiguration, soc_update_data: SocUpdateData) -> CarState:
    log.debug("Fetching Tronity SOC")
    session = create_session(str(config.client_id), str(config.client_secret))
    vehicle_id = str(config.vehicle_id)
    tronity_data = fetch_soc_for_vehicle(vehicle_id, session)
    return CarState(soc=tronity_data['level'], range=tronity_data['range'], soc_timestamp=tronity_data['lastUpdate'])


def create_session(client_id: str, client_secret: str) -> req.Session:
    session = req.Session()
    data = {'grant_type': 'app',
            'client_id': str(client_id),
            'client_secret': str(client_secret)}

    response = session.post(
        "https://api.tronity.tech/authentication",
        data=data,
    )

    if response.status_code != 201:
        raise Exception("Error requesting Tronity access token, please check client_id and client_secret: %s"
                        % response.status_code)

    access_token = response.json()['access_token']
    session.headers = {
        'Accept': 'application/hal+json', 'Authorization': 'Bearer %s' % access_token
    }
    log.debug("Retrieved Tronity Access Token.")
    return session


def fetch_vehicles(session: req.Session) -> dict:
    url = 'https://api.tronity.tech/tronity/vehicles'
    vehicles = session.get(url).json()
    if vehicles.status_code != 200:
        raise Exception("Error requesting vehicles from Tronity: %s" % vehicles.status_code)

    log.debug("Retrieved Tronity vehicles: %s", vehicles["data"])
    return vehicles["data"]


def fetch_soc_for_vehicle(vehicle_id: str, session: req.Session) -> dict:
    url = 'https://api.tronity.tech/tronity/vehicles/' + str(vehicle_id) + '/last_record'
    response = session.get(url).json()
    if response.status_code != 200:
        raise Exception("Error requesting vehicle from Tronity: %s" % response.status_code)
    log.debug("Retrieved Tronity data: %s", response)
    return response
