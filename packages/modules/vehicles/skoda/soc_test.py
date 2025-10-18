from unittest.mock import Mock, MagicMock
import pytest
import asyncio
from modules.common import store
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_context import SingleComponentUpdateContext
from modules.vehicles.skoda import api
from modules.vehicles.skoda.soc import create_vehicle
from modules.vehicles.skoda.config import Skoda, SkodaConfiguration
from modules.vehicles.skoda.libskoda import skoda as SkodaApi


class TestSkoda:
    @pytest.fixture(autouse=True)
    def set_up(self, monkeypatch):
        self.mock_context_exit = Mock(return_value=True)
        self.mock_fetch_soc = Mock(name="fetch_soc", return_value=(50, 250, "2025-10-18T10:00:00Z", 1760822400.0))
        self.mock_value_store = Mock(name="value_store")
        monkeypatch.setattr(api, "fetch_soc", self.mock_fetch_soc)
        monkeypatch.setattr(store, "get_car_value_store", Mock(return_value=self.mock_value_store))
        monkeypatch.setattr(SingleComponentUpdateContext, '__exit__', self.mock_context_exit)

    def test_update_updates_value_store(self):
        # setup
        config = Skoda(configuration=SkodaConfiguration(user_id="test_user", password="test_password", vin="test_vin"))
        
        # execution
        create_vehicle(config, 1).update(VehicleUpdateData())

        # evaluation
        self.assert_context_manager_called_with(None)
        self.mock_fetch_soc.assert_called_once_with(config, 1)
        assert self.mock_value_store.set.call_count == 1
        call_args = self.mock_value_store.set.call_args[0][0]
        assert call_args.soc == 50
        assert call_args.range == 250
        assert call_args.soc_timestamp == 1760822400.0

    def test_update_passes_errors_to_context(self):
        # setup
        dummy_error = Exception("API Error")
        self.mock_fetch_soc.side_effect = dummy_error
        config = Skoda(configuration=SkodaConfiguration(user_id="test_user", password="test_password", vin="test_vin"))

        # execution
        create_vehicle(config, 1).update(VehicleUpdateData())

        # evaluation
        self.assert_context_manager_called_with(dummy_error)

    def assert_context_manager_called_with(self, error):
        assert self.mock_context_exit.call_count == 1
        assert self.mock_context_exit.call_args[0][1] is error


class MockAiohttpResponse:
    def __init__(self, json_data, status_code):
        self._json_data = json_data
        self.status = status_code

    async def json(self):
        return self._json_data

    def release(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass


class TestSkodaGetStatus:
    @pytest.fixture
    def mock_session(self):
        session = MagicMock()

        async def get_side_effect(*args, **kwargs):
            return session.get.return_value
        session.get = MagicMock(side_effect=get_side_effect)
        return session

    @pytest.fixture
    def skoda_instance(self, mock_session):
        instance = SkodaApi(mock_session)
        instance.set_vin("test_vin")
        instance.headers = {"Authorization": "Bearer test_token"}
        return instance

    def test_get_status_success_primary_url(self, skoda_instance, mock_session):
        # setup
        response_data = {
            "carType": "electric",
            "totalRangeInKm": 291,
            "primaryEngineRange": {
                "engineType": "electric",
                "currentSoCInPercent": 66,
                "remainingRangeInKm": 291
            },
            "carCapturedTimestamp": "2025-10-17T15:40:35.679Z"
        }
        mock_session.get.return_value = MockAiohttpResponse(response_data, 200)

        # execution
        status = asyncio.run(skoda_instance.get_status())

        # evaluation
        assert status['charging']['batteryStatus']['value']['currentSOC_pct'] == 66
        assert status['charging']['batteryStatus']['value']['cruisingRangeElectric_km'] == 291
        assert status['charging']['batteryStatus']['value']['carCapturedTimestamp'] == "2025-10-17T15:40:35Z"
        mock_session.get.assert_called_once_with(
            "https://mysmob.api.connect.skoda-auto.cz/api/v2/vehicle-status/test_vin/driving-range",
            headers=skoda_instance.headers
        )

    def test_get_status_fallback_to_charging_url(self, skoda_instance, mock_session):
        # setup
        vehicle_status_response_data = {
            "carType": "electric",
            "primaryEngineRange": {
                "engineType": "electric",
                "currentSoCInPercent": 42
            },
            "carCapturedTimestamp": "2025-09-26T11:00:25.848Z"
        }
        charging_url_response_data = {
            "isVehicleInSavedLocation": False,
            "status": {
                "chargingRateInKilometersPerHour": 0.0,
                "chargePowerInKw": 0.0,
                "remainingTimeToFullyChargedInMinutes": 0,
                "battery": {
                    "remainingCruisingRangeInMeters": 291000,
                    "stateOfChargeInPercent": 66
                }
            },
            "settings": {
                "targetStateOfChargeInPercent": 80,
                "preferredChargeMode": "MANUAL",
                "availableChargeModes": [
                    "MANUAL"
                ],
                "chargingCareMode": "ACTIVATED",
                "autoUnlockPlugWhenCharged": "OFF",
                "maxChargeCurrentAc": "MAXIMUM"
            },
            "carCapturedTimestamp": "2025-10-17T15:38:55Z",
            "errors": [
                {
                    "type": "STATUS_OF_CHARGING_NOT_AVAILABLE",
                    "description": "Status of charging is not available."
                }
            ]
        }
        responses = [
            MockAiohttpResponse(vehicle_status_response_data, 200),
            MockAiohttpResponse(charging_url_response_data, 200)
        ]

        async def side_effect_func(*args, **kwargs):
            return responses.pop(0)
        mock_session.get.side_effect = side_effect_func

        # execution
        status = asyncio.run(skoda_instance.get_status())

        # evaluation
        assert status['charging']['batteryStatus']['value']['currentSOC_pct'] == 66
        assert status['charging']['batteryStatus']['value']['cruisingRangeElectric_km'] == 291.0
        assert status['charging']['batteryStatus']['value']['carCapturedTimestamp'] == "2025-10-17T15:38:55Z"
        assert mock_session.get.call_count == 2
        mock_session.get.assert_any_call(
            "https://mysmob.api.connect.skoda-auto.cz/api/v2/vehicle-status/test_vin/driving-range",
            headers=skoda_instance.headers
        )
        mock_session.get.assert_any_call(
            "https://mysmob.api.connect.skoda-auto.cz/api/v1/charging/test_vin",
            headers=skoda_instance.headers
        )

    def test_get_status_timestamp_without_milliseconds(self, skoda_instance, mock_session):
        # setup
        response_data = {
            "carType": "hybrid",
            "totalRangeInKm": 647,
            "primaryEngineRange": {
                "engineType": "gasoline",
                "currentSoCInPercent": 100,
                "currentFuelLevelInPercent": 100,
                "remainingRangeInKm": 600
            },
            "secondaryEngineRange": {
                "engineType": "electric",
                "currentSoCInPercent": 42,
                "currentFuelLevelInPercent": 88,
                "remainingRangeInKm": 47
            },
            "carCapturedTimestamp": "2025-10-06T10:12:44Z"
        }
        mock_session.get.return_value = MockAiohttpResponse(response_data, 200)

        # execution
        status = asyncio.run(skoda_instance.get_status())

        # evaluation
        assert status['charging']['batteryStatus']['value']['currentSOC_pct'] == 42
        assert status['charging']['batteryStatus']['value']['cruisingRangeElectric_km'] == 47
        assert status['charging']['batteryStatus']['value']['carCapturedTimestamp'] == "2025-10-06T10:12:44Z"
