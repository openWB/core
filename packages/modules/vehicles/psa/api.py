#!/usr/bin/env python3

import logging
from typing import Optional

from modules.common import req
from typing import NamedTuple, Tuple

from modules.vehicles.psa.config import PSAConfiguration

log = logging.getLogger(__name__)

ManufacturerConfiguration = NamedTuple(
    "ManufacturerConfiguration",
    [("brand", str), ("realm", str), ("client_id", Optional[str]), ("client_secret", Optional[str])]
)

manufacturer_configurations = {
    "Peugeot": ManufacturerConfiguration(
        brand="peugeot.com",
        realm="clientsB2CPeugeot",
        client_id="1eebc2d5-5df3-459b-a624-20abfcf82530",
        client_secret="T5tP7iS0cO8sC0lA2iE2aR7gK6uE5rF3lJ8pC3nO1pR7tL8vU1",
    ),
    "Citroen": ManufacturerConfiguration(
        brand="citroen.com",
        realm="clientsB2CCitroen",
        client_id="5364defc-80e6-447b-bec6-4af8d1542cae",
        client_secret="iE0cD8bB0yJ0dS6rO3nN1hI2wU7uA5xR4gP7lD6vM0oH0nS8dN",
    ),
    "DS": ManufacturerConfiguration(
        brand="driveds.com",
        realm="clientsB2CDS",
        client_id="cbf74ee7-a303-4c3d-aba3-29f5994e2dfa",
        client_secret="X6bE6yQ3tH1cG5oA6aW4fS6hK0cR0aK5yN2wE4hP8vL8oW5gU3",
    ),
    "Opel": ManufacturerConfiguration(
        brand="opel.com",
        realm="clientsB2COpel",
        client_id="07364655-93cb-4194-8158-6b035ac2c24c",
        client_secret="F2kK7lC5kF5qN7tM0wT8kE3cW1dP0wC5pI6vC0sQ5iP5cN8cJ8",
    ),
    "Vauxhall": ManufacturerConfiguration(
        brand="vauxhall.co.uk",
        realm="clientsB2CVauxhall",
        client_id=None,  # don't have valid client_id and secret for Vauxhall
        client_secret=None,  # don't have valid client_id and secret for Vauxhall
    )
}


def create_session(user_id: str, password: str, client_id: Optional[str], client_secret: Optional[str],
                   manufacturer: str) -> req.Session:
    manufacturer_config = manufacturer_configurations[manufacturer]
    brand = manufacturer_config.brand
    realm = manufacturer_config.realm
    if not client_id or not client_secret:  # use defaults if no client_id and client_secret is specified
        client_id = manufacturer_config.client_id
        client_secret = manufacturer_config.client_secret
        if not client_id or not client_secret:
            raise Exception(
                "No OAuth credentials configured and no default available for manufacturer %s" % manufacturer)

    session = req.get_http_session()
    data = {
        'realm': realm, 'grant_type': 'password', 'password': password, 'username': user_id, 'scope': 'openid profile'
    }

    access_token = session.post(
        "https://idpcvs." + str(brand) + "/am/oauth2/access_token", data=data, auth=(client_id, client_secret)
    ).json()['access_token']

    session.params = {"client_id": client_id}
    session.headers = {
        'Accept': 'application/hal+json', 'Authorization': 'Bearer %s' % access_token, 'x-introspect-realm': realm
    }
    return session


def fetch_vehicle(vin: str, session: req.Session) -> dict:

    vehicle_response = session.get(
        "https://api.groupe-psa.com/connectedcar/v4/user/vehicles").json()
    vehicles = vehicle_response['_embedded']['vehicles']

    # Filter list for given VIN or select first entry if no VIN is provided
    try:
        vehicle_selected = next(
            vehicle for vehicle in vehicles if vehicle['vin'] == vin) if vin else vehicles[0]
    except StopIteration:
        raise Exception("Cannot find VIN: '" + str(vin) + "'")

    return vehicle_selected


def fetch_energy(vin_id: str, session: req.Session) -> dict:
    battery = session.get(
        "https://api.groupe-psa.com/connectedcar/v4/user/vehicles/" + str(vin_id) + "/status").json()

    # filter to only include type=Electric but remove all others. Seen type=Fuel and type=Electric being returned.
    energies = battery['energy']
    energy_selected = next(energy for energy in energies if energy['type'] == 'Electric')
    return energy_selected


def fetch_soc(config: PSAConfiguration,
              vehicle_id: int) -> Tuple[float, float, str]:

    try:
        session = create_session(
            config.user_id, config.password, config.client_id, config.client_secret, config.manufacturer)

        vehicle = fetch_vehicle(config.vin, session)
        log.debug("Fetching details for VIN: %s with vehicle_id: %s", vehicle['vin'], vehicle['id'])
        energy = fetch_energy(vehicle['id'], session)

    except Exception:
        raise Exception("Error requesting PSA data for vehicle: %s" % vehicle_id)
    log.info("psa.fetch_soc: soc=%s%%, range=%s, timestamp=%s",
             energy['level'], energy['autonomy'], energy['updatedAt'])
    return energy['level'], energy['autonomy'], energy['updatedAt']
