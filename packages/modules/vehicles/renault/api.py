#!/usr/bin/env python3

import logging
from modules.common.component_state import CarState
from modules.common import req
from modules.vehicles.renault.config import RenaultConfiguration

log = logging.getLogger(__name__)

GIGYA_ROOTURL = 'https://accounts.eu1.gigya.com'
GIGYA_API = '3_VgdkgtIRH3AdHvJm-cjV2ug2EFE0lxt0IJzMC4MFqZjFpn_GYFXVdNZ19L7wZX0N'
KAMEREON_ROOTURL = 'https://api-wired-prod-1-euw1.wrd-aws.com'
KAMEREON_API_KEY = 'YjkKtHmGfaceeuExUDKGxrLZGGvtVS0J'


def fetch_soc(config: RenaultConfiguration) -> CarState:
    country_data = {'country': config.country}
    # eine Session für den gesamten Login-/Abfrageablauf verwenden, da Renault/Gigya
    # sitzungsübergreifend gesetzte Cookies für die Folgeaufrufe benötigt
    session = req.get_http_session()

    # Gigya-Login: Zugangsdaten gegen Session-Cookie tauschen
    payload = {'loginID': config.user_id, 'password': config.password, 'apiKey': GIGYA_API}
    gigya_session = session.post(f"{GIGYA_ROOTURL}/accounts.login", data=payload).json()
    gigyacookievalue = gigya_session['sessionInfo']['cookieValue']

    # Account-Infos abrufen (liefert personId)
    payload = {'login_token': gigyacookievalue, 'apiKey': GIGYA_API}
    gigya_account = session.post(f"{GIGYA_ROOTURL}/accounts.getAccountInfo", data=payload).json()

    # JWT für Kamereon-API anfordern
    payload = {'login_token': gigyacookievalue, 'apiKey': GIGYA_API,
               'fields': 'data.personId,data.gigyaDataCenter', 'expiration': 900}
    gigya_jwt = session.post(f"{GIGYA_ROOTURL}/accounts.getJWT", data=payload).json()
    gigya_jwttoken = gigya_jwt['id_token']

    # Kamereon-Account anhand der personId ermitteln
    kamereonpersonid = gigya_account['data']['personId']
    headers = {'x-gigya-id_token': gigya_jwttoken, 'apikey': KAMEREON_API_KEY}
    kamereon_per = session.get(f"{KAMEREON_ROOTURL}/commerce/v1/persons/{kamereonpersonid}",
                               headers=headers, params=country_data).json()
    kamereonaccountid = kamereon_per['accounts'][0]['accountId']
    log.debug(f"account id {kamereonaccountid}")

    # Fahrzeugliste abrufen, um VIN zu ermitteln, falls nicht konfiguriert
    vehic = session.get(
        f"{KAMEREON_ROOTURL}/commerce/v1/accounts/{kamereonaccountid}/vehicles",
        headers=headers, params=country_data).json()
    if config.vin is None or len(config.vin) < 10:
        vin = vehic['vehicleLinks'][0]['vin']
    else:
        vin = config.vin

    # Batteriestatus abrufen (SoC, Reichweite)
    batt = session.get(
        f"{KAMEREON_ROOTURL}/commerce/v1/accounts/{kamereonaccountid}/kamereon/kca/"
        f"car-adapter/v2/cars/{vin}/battery-status",
        headers=headers, params=country_data).json()

    # Cockpit-Daten abrufen (Kilometerstand); nicht jedes Fahrzeug liefert diesen Wert
    odometer = None
    try:
        cockpit = session.get(
            f"{KAMEREON_ROOTURL}/commerce/v1/accounts/{kamereonaccountid}/kamereon/kca/"
            f"car-adapter/v1/cars/{vin}/cockpit",
            headers=headers, params=country_data).json()
        odometer = float(cockpit['data']['attributes']['totalMileage'])
    except Exception:
        log.debug("Kilometerstand konnte nicht abgerufen werden.", exc_info=True)

    return CarState(soc=float(batt['data']['attributes']['batteryLevel']),
                    range=float(batt['data']['attributes']['batteryAutonomy']),
                    odometer=odometer)
