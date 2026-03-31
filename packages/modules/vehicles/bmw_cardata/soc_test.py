from unittest.mock import Mock, patch
import pytest
from modules.common import store
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_context import SingleComponentUpdateContext
from modules.vehicles.bmw_cardata.soc import create_vehicle, fetch_soc
from modules.vehicles.bmw_cardata.config import BmwCardataSetup, BmwCardataConfiguration


class TestBmwCardata:
    @pytest.fixture(autouse=True)
    def set_up(self, monkeypatch):
        self.mock_context_exit = Mock(return_value=True)
        self.mock_value_store = Mock(name="value_store")
        monkeypatch.setattr(store, "get_car_value_store", Mock(return_value=self.mock_value_store))
        monkeypatch.setattr(SingleComponentUpdateContext, '__exit__', self.mock_context_exit)

    def _make_config(self, test_mode=True, **kwargs):
        return BmwCardataSetup(
            configuration=BmwCardataConfiguration(
                client_id="test-client-id",
                vin="WBY00000000000000",
                test_mode=test_mode,
                test_soc=80,
                test_range=300,
                access_token="test-token" if not test_mode else "",
                refresh_token="test-refresh",
                expires_at=9999999999,
                **kwargs
            )
        )

    def test_testmode_returns_test_values(self):
        config = self._make_config(test_mode=True)
        result = fetch_soc(config)
        assert result.soc == 80
        assert result.range == 300

    def test_testmode_custom_values(self):
        config = BmwCardataSetup(
            configuration=BmwCardataConfiguration(
                test_mode=True,
                test_soc=42,
                test_range=150,
            )
        )
        result = fetch_soc(config)
        assert result.soc == 42
        assert result.range == 150

    def test_update_in_testmode(self):
        create_vehicle(self._make_config(test_mode=True), 0).update(VehicleUpdateData())
        assert self.mock_value_store.set.call_count == 1
        assert self.mock_value_store.set.call_args[0][0].soc == 80
        assert self.mock_value_store.set.call_args[0][0].range == 300

    def test_missing_client_id_raises(self):
        config = BmwCardataSetup(
            configuration=BmwCardataConfiguration(
                test_mode=False,
                client_id="",
                vin="WBY00000000000000",
            )
        )
        with pytest.raises(Exception, match="client_id"):
            fetch_soc(config)

    def test_missing_vin_raises(self):
        config = BmwCardataSetup(
            configuration=BmwCardataConfiguration(
                test_mode=False,
                client_id="test-client-id",
                vin="",
            )
        )
        with pytest.raises(Exception, match="VIN"):
            fetch_soc(config)

    def test_missing_token_raises(self):
        config = BmwCardataSetup(
            configuration=BmwCardataConfiguration(
                test_mode=False,
                client_id="test-client-id",
                vin="WBY00000000000000",
                access_token="",
            )
        )
        with pytest.raises(Exception, match="Tokens"):
            fetch_soc(config)

    def test_api_error_passes_to_context(self, monkeypatch):
        dummy_error = Exception("BMW CarData: Tageslimit erreicht (CU-429).")
        monkeypatch.setattr(
            "modules.vehicles.bmw_cardata.soc.http_get",
            Mock(side_effect=dummy_error)
        )
        monkeypatch.setattr(
            "modules.vehicles.bmw_cardata.soc.get_container_id",
            Mock(return_value="test-container-id")
        )
        create_vehicle(self._make_config(test_mode=False), 0).update(VehicleUpdateData())
        assert self.mock_context_exit.call_count == 1

    def test_soc_extraction_primary_field(self, monkeypatch):
        mock_response = {
            "telematicData": {
                "vehicle.drivetrain.electricEngine.charging.level": {"value": "75", "unit": "%"},
                "vehicle.drivetrain.electricEngine.remainingElectricRange": {"value": "350", "unit": "km"},
                "vehicle.drivetrain.electricEngine.charging.status": {"value": "NOCHARGING", "unit": None},
                "vehicle.vehicle.travelledDistance": {"value": "61570", "unit": "km"},
            }
        }
        monkeypatch.setattr("modules.vehicles.bmw_cardata.soc.http_get", Mock(return_value=mock_response))
        monkeypatch.setattr("modules.vehicles.bmw_cardata.soc.get_container_id", Mock(return_value="test-id"))

        result = fetch_soc(self._make_config(test_mode=False))
        assert result.soc == 75
        assert result.range == 350
        assert result.odometer == 61570

    def test_soc_extraction_fallback_field(self, monkeypatch):
        mock_response = {
            "telematicData": {
                "vehicle.drivetrain.batteryManagement.header": {"value": "63", "unit": "%"},
                "vehicle.drivetrain.electricEngine.remainingElectricRange": {"value": "280", "unit": "km"},
                "vehicle.drivetrain.electricEngine.charging.status": {"value": "CHARGINGACTIVE", "unit": None},
            }
        }
        monkeypatch.setattr("modules.vehicles.bmw_cardata.soc.http_get", Mock(return_value=mock_response))
        monkeypatch.setattr("modules.vehicles.bmw_cardata.soc.get_container_id", Mock(return_value="test-id"))

        result = fetch_soc(self._make_config(test_mode=False))
        assert result.soc == 63
        assert result.range == 280

    def test_no_soc_raises(self, monkeypatch):
        mock_response = {"telematicData": {}}
        monkeypatch.setattr("modules.vehicles.bmw_cardata.soc.http_get", Mock(return_value=mock_response))
        monkeypatch.setattr("modules.vehicles.bmw_cardata.soc.get_container_id", Mock(return_value="test-id"))

        with pytest.raises(Exception, match="Kein SoC"):
            fetch_soc(self._make_config(test_mode=False))
