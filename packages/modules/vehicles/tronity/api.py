#!/usr/bin/env python3
import logging
import jwt

from dataclass_utils import asdict
from helpermodules.pub import Pub
from modules.common import req
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.vehicles.tronity.config import TronityVehicleSocConfiguration, TronityVehicleSoc
from modules.common.component_state import CarState
from datetime import datetime

log = logging.getLogger(__name__)


def fetch_soc(config: TronityVehicleSocConfiguration, vehicle_update_data: VehicleUpdateData, vehicle: int) -> CarState:
    log.debug("Fetching Tronity SOC")
    session = create_session(config, vehicle)
    tronity_vehicle_id = str(config.vehicle_id)
    tronity_data = fetch_soc_for_vehicle(tronity_vehicle_id, session)
    return CarState(soc=tronity_data['level'], range=tronity_data['range'], soc_timestamp=tronity_data['lastUpdate'])


def is_token_valid(access_token: str) -> bool:
    if not access_token or access_token == 'None':
        log.debug("No token found")
        return False
    else:
        log.debug("Found Token: %s", access_token)

    decoded_data = jwt.decode(jwt=access_token, verify=False, algorithms=['HS256'], options={"verify_signature": False})
    if datetime.utcfromtimestamp(decoded_data['exp']) < datetime.utcnow():
        log.debug("Token expired: %s", decoded_data)
        return False
    else:
        log.debug("Token still valid: %s", decoded_data)
        return True


def write_token_mqtt(topic: str, token: str, config: TronityVehicleSocConfiguration):
    try:
        config.access_token = token
        value: TronityVehicleSoc = TronityVehicleSoc(configuration=config)
        log.debug("saving new access token")
        Pub().pub(topic, asdict(value))
    except Exception as e:
        log.exception('Token mqtt write exception ' + str(e))


def create_session(config: TronityVehicleSocConfiguration, vehicle: int) -> req.Session:
    session = req.Session()
    data = {'grant_type': 'app',
            'client_id': str(config.client_id),
            'client_secret': str(config.client_secret)}

    if not is_token_valid(str(config.access_token)):
        log.debug("Requesting new Tronity Access Token")
        response = session.post(
            "https://api.tronity.tech/authentication",
            data=data,
        )

        if response.status_code != 201:
            raise Exception("Error requesting Tronity access token, please check client_id and client_secret: %s"
                            % response.status_code)

        access_token = response.json()['access_token']
        log.debug("Retrieved new Tronity Access Token: %s", access_token)
        write_token_mqtt(
            "openWB/set/vehicle/" + str(vehicle) + "/soc_module/config",
            access_token,
            config)
    else:
        log.debug("Using existing Tronity Access Token")
        access_token = config.access_token

    session.headers = {
        'Accept': 'application/hal+json', 'Authorization': 'Bearer %s' % access_token
    }
    return session


def fetch_vehicles(session: req.Session) -> dict:
    url = 'https://api.tronity.tech/tronity/vehicles'
    response = session.get(url)
    if response.status_code != 200:
        raise Exception("Error requesting vehicles from Tronity: %s" % response.status_code)
    vehicles = response.json()
    log.debug("Retrieved Tronity vehicles: %s", vehicles["data"])
    return vehicles["data"]


def fetch_soc_for_vehicle(vehicle_id: str, session: req.Session) -> dict:
    url = 'https://api.tronity.tech/tronity/vehicles/' + str(vehicle_id) + '/last_record'
    response = session.get(url)
    if response.status_code != 200:
        raise Exception("Error requesting vehicle from Tronity: %s" % response.status_code)
    data = response.json()
    log.debug("Retrieved Tronity data: %s", data)
    return data
