from unittest.mock import Mock, MagicMock
import pytest
import asyncio
from modules.common import store
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_context import SingleComponentUpdateContext
from modules.vehicles.cupra import api
from modules.vehicles.cupra.soc import create_vehicle
from modules.vehicles.cupra.config import Cupra, CupraConfiguration
from modules.vehicles.cupra.libcupra import cupra as CupraApi


class TestCupra:
    @pytest.fixture(autouse=True)
    def set_up(self, monkeypatch):
        self.mock_context_exit = Mock(return_value=True)
        self.mock_fetch_soc = Mock(
            name="fetch_soc",
            return_value=(60, 320, "2026-03-29T11:00:00Z", 1774782000.0, 45678),
        )
        self.mock_value_store = Mock(name="value_store")
        monkeypatch.setattr(api, "fetch_soc", self.mock_fetch_soc)
        monkeypatch.setattr(store, "get_car_value_store", Mock(return_value=self.mock_value_store))
        monkeypatch.setattr(SingleComponentUpdateContext, '__exit__', self.mock_context_exit)

    def test_update_updates_value_store(self):
        # setup
        config = Cupra(configuration=CupraConfiguration(user_id="test_user", password="test_password", vin="test_vin"))

        # execution
        create_vehicle(config, 1).update(VehicleUpdateData())

        # evaluation
        self.assert_context_manager_called_with(None)
        self.mock_fetch_soc.assert_called_once_with(config, 1)
        assert self.mock_value_store.set.call_count == 1
        call_args = self.mock_value_store.set.call_args[0][0]
        assert call_args.soc == 60
        assert call_args.range == 320
        assert call_args.soc_timestamp == 1774782000.0
        assert call_args.odometer == 45678

    def test_update_passes_errors_to_context(self):
        # setup
        dummy_error = Exception("Der SoC kann nicht ausgelesen werden")
        self.mock_fetch_soc.side_effect = dummy_error
        config = Cupra(configuration=CupraConfiguration(user_id="test_user", password="test_password", vin="test_vin"))

        # execution
        create_vehicle(config, 1).update(VehicleUpdateData())

        # evaluation
        self.assert_context_manager_called_with_substr(dummy_error)

    def assert_context_manager_called_with(self, error):
        assert self.mock_context_exit.call_count == 1
        assert self.mock_context_exit.call_args[0][1] is error

    def assert_context_manager_called_with_substr(self, error):
        assert self.mock_context_exit.call_count == 1
        assert str(error) in str(self.mock_context_exit.call_args[0][1])


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


class TestCupraGetStatus:
    @pytest.fixture
    def mock_session(self):
        session = MagicMock()

        async def get_side_effect(*args, **kwargs):
            return session.get.return_value
        session.get = MagicMock(side_effect=get_side_effect)
        return session

    @pytest.fixture
    def cupra_instance(self, mock_session):
        instance = CupraApi(mock_session)
        instance.set_vin("test_vin")
        instance.headers = {"Authorization": "Bearer test_token"}
        return instance

    def test_get_status_success(self, cupra_instance, mock_session):
        # setup
        status_response_data = {
            "status": {
                "battery": {
                    "currentSOC_pct": 67,
                    "cruisingRangeElectric_km": 305,
                    "carCapturedTimestamp": "2026-03-29T11:20:00Z"
                }
            }
        }
        mileage_response_data = {
            "mileageKm": 77889
        }
        responses = [
            MockAiohttpResponse(status_response_data, 200),
            MockAiohttpResponse(mileage_response_data, 200)
        ]

        async def side_effect_func(*args, **kwargs):
            return responses.pop(0)
        mock_session.get.side_effect = side_effect_func

        # execution
        status = asyncio.run(cupra_instance.get_status())

        # evaluation
        assert status['charging']['batteryStatus']['value']['currentSOC_pct'] == 67
        assert status['charging']['batteryStatus']['value']['cruisingRangeElectric_km'] == 305
        assert status['charging']['batteryStatus']['value']['carCapturedTimestamp'] == "2026-03-29T11:20:00Z"
        assert status['charging']['batteryStatus']['value']['odometer'] == 77889
        assert mock_session.get.call_count == 2
        mock_session.get.assert_any_call(
            "https://ola.prod.code.seat.cloud.vwgroup.com/vehicles/test_vin/charging/status",
            headers=cupra_instance.headers
        )
        mock_session.get.assert_any_call(
            "https://ola.prod.code.seat.cloud.vwgroup.com/v1/vehicles/test_vin/mileage",
            headers=cupra_instance.headers
        )

    def test_get_status_mileage_error_sets_odometer_none(self, cupra_instance, mock_session):
        # setup
        status_response_data = {
            "status": {
                "battery": {
                    "currentSOC_pct": 67,
                    "cruisingRangeElectric_km": 305,
                    "carCapturedTimestamp": "2026-03-29T11:20:00Z"
                }
            }
        }
        mileage_error_response = {
            "error": "service_unavailable"
        }
        responses = [
            MockAiohttpResponse(status_response_data, 200),
            MockAiohttpResponse(mileage_error_response, 503)
        ]

        async def side_effect_func(*args, **kwargs):
            return responses.pop(0)
        mock_session.get.side_effect = side_effect_func

        # execution
        status = asyncio.run(cupra_instance.get_status())

        # evaluation
        assert status['charging']['batteryStatus']['value']['currentSOC_pct'] == 67
        assert status['charging']['batteryStatus']['value']['cruisingRangeElectric_km'] == 305
        assert status['charging']['batteryStatus']['value']['carCapturedTimestamp'] == "2026-03-29T11:20:00Z"
        assert status['charging']['batteryStatus']['value']['odometer'] is None
