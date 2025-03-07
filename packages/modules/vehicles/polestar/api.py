import logging
from modules.common import req
import time
from modules.vehicles.polestar.auth import PolestarAuth
from modules.common.component_state import CarState


log = logging.getLogger(__name__)


class PolestarApi:

    def __init__(self, username: str, password: str, vin: str) -> None:
        self.auth = PolestarAuth(username, password, vin)
        self.vin = vin
        self.client_session = req.get_http_session()

    def query_params(self, params: dict, url='https://pc-api.polestar.com/eu-north-1/mystar-v2/') -> dict or None:
        access_token = self.auth.get_auth_token()
        if access_token is None:
            raise Exception("query_params error:could not get auth token")

        headers = {
            "Content-Type": "application/json",
            "authorization": f"Bearer {self.auth.access_token}"
        }

        log.info("query_params:%s", params['query'])
        try:
            result = self.client_session.get(url=url, params=params, headers=headers)
        except Exception as e:
            if result.status_code == 401:
                self.auth.delete_token()
            if self.auth.access_token is not None:
                # if we got an access code but the query failed, VIN could be wrong, so let`s check it
                self.check_vin()
            raise e

        result_data = result.json()
        if result_data.get('errors'):
            error_message = result_data['errors'][0]['message']
            raise Exception("query_params error: %s", error_message)

        return result_data

    def get_battery_data(self) -> dict or None:
        params = {
            "query": "query GetBatteryData($vin: String!) { getBatteryData(vin: $vin) { "
            + "batteryChargeLevelPercentage  estimatedDistanceToEmptyKm } }",
            "operationName": "GetBatteryData",
            "variables": "{\"vin\":\"" + self.vin + "\"}"
        }

        result = self.query_params(params)

        return result['data']['getBatteryData']

    def check_vin(self) -> None:
        # get Vehicle Data
        params = {
            "query": "query GetConsumerCarsV2 { getConsumerCarsV2 { vin internalVehicleIdentifier __typename }}",
            "operationName": "GetConsumerCarsV2",
            "variables": "{}"
        }
        result = self.query_params(params, url='https://pc-api.polestar.com/eu-north-1/my-star/')
        if result is not None and result['data'] is not None:
            vins = []
            # get list of cars and store the ones not matching our vin
            cars = result['data']['getConsumerCarsV2']
            if len(cars) == 0:
                raise Exception("Es konnten keine Fahrzeuge im Account gefunden werden. Bitte in den Einstellungen " +
                                "prüfen, ob der Besitzer-Account des Polestars eingetragen ist.")

            for i in range(0, len(cars)):
                if cars[i]['vin'] == self.vin:
                    pass
                else:
                    vins.append(cars[i]['vin'])
            if len(vins) > 0:
                raise Exception("You probably specified a wrong VIN. We only found:%s", ",".join(vins))


def fetch_soc(user_id: str, password: str, vin: str, vehicle: int) -> CarState:
    api = PolestarApi(user_id, password, vin)
    bat_data = api.get_battery_data()
    soc = bat_data['batteryChargeLevelPercentage']
    est_range = bat_data['estimatedDistanceToEmptyKm']

    return CarState(soc, est_range, time.strftime("%m/%d/%Y, %H:%M:%S"))
