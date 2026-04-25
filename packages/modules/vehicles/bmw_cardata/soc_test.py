import pytest
from unittest.mock import Mock

from requests.exceptions import HTTPError as RequestsHTTPError

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
        monkeypatch.setattr(SingleComponentUpdateContext, "__exit__", self.mock_context_exit)

    def _make_config(self, **kwargs):
        defaults = dict(
            client_id="test-client-id",
            vin="WBY00000000000000",
            access_token="test-token",
            refresh_token="test-refresh",
            expires_at=9999999999,
            container_id="test-container-id",
        )
        defaults.update(kwargs)
        return BmwCardataSetup(
            configuration=BmwCardataConfiguration(**defaults)
        )

    def test_missing_client_id_raises(self):
        config = BmwCardataSetup(
            configuration=BmwCardataConfiguration(
                client_id="",
                vin="WBY00000000000000",
                access_token="test-token",
            )
        )
        with pytest.raises(Exception, match="client_id"):
            fetch_soc(config)

    def test_missing_vin_raises(self):
        config = BmwCardataSetup(
            configuration=BmwCardataConfiguration(
                client_id="test-client-id",
                vin="",
                access_token="test-token",
            )
        )
        with pytest.raises(Exception, match="VIN"):
            fetch_soc(config)

    def test_missing_token_raises(self):
        config = BmwCardataSetup(
            configuration=BmwCardataConfiguration(
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
            "modules.vehicles.bmw_cardata.soc.req.get_http_session",
            Mock(side_effect=dummy_error)
        )
        create_vehicle(self._make_config(), 0).update(VehicleUpdateData())
        assert self.mock_context_exit.call_count == 1

    def test_soc_extraction_primary_field(self, monkeypatch):
        mock_response = Mock()
        mock_response.json.return_value = {
            "telematicData": {
                "vehicle.drivetrain.electricEngine.charging.level": {"value": "75", "unit": "%"},
                "vehicle.drivetrain.electricEngine.remainingElectricRange": {"value": "350", "unit": "km"},
                "vehicle.drivetrain.electricEngine.charging.status": {"value": "NOCHARGING", "unit": None},
                "vehicle.vehicle.travelledDistance": {"value": "61570", "unit": "km"},
            }
        }
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session.headers = {}
        monkeypatch.setattr("modules.vehicles.bmw_cardata.soc.req.get_http_session", Mock(return_value=mock_session))

        result = fetch_soc(self._make_config())
        assert result.soc == 75
        assert result.range == 350
        assert result.odometer == 61570

    def test_soc_extraction_fallback_field(self, monkeypatch):
        mock_response = Mock()
        mock_response.json.return_value = {
            "telematicData": {
                "vehicle.drivetrain.batteryManagement.header": {"value": "63", "unit": "%"},
                "vehicle.drivetrain.electricEngine.remainingElectricRange": {"value": "280", "unit": "km"},
                "vehicle.drivetrain.electricEngine.charging.status": {"value": "CHARGINGACTIVE", "unit": None},
            }
        }
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session.headers = {}
        monkeypatch.setattr("modules.vehicles.bmw_cardata.soc.req.get_http_session", Mock(return_value=mock_session))

        result = fetch_soc(self._make_config())
        assert result.soc == 63
        assert result.range == 280

    def test_no_soc_raises(self, monkeypatch):
        mock_response = Mock()
        mock_response.json.return_value = {"telematicData": {}}
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session.headers = {}
        monkeypatch.setattr("modules.vehicles.bmw_cardata.soc.req.get_http_session", Mock(return_value=mock_session))

        with pytest.raises(Exception, match="Kein SoC"):
            fetch_soc(self._make_config())

    def test_token_refresh_on_expired(self, monkeypatch):
        mock_response = Mock()
        mock_response.json.return_value = {
            "telematicData": {
                "vehicle.drivetrain.electricEngine.charging.level": {"value": "55", "unit": "%"},
                "vehicle.drivetrain.electricEngine.remainingElectricRange": {"value": "270", "unit": "km"},
            }
        }
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session.post.return_value = Mock(json=Mock(return_value={
            "access_token": "new-token",
            "refresh_token": "new-refresh",
            "expires_in": 3600,
        }))
        mock_session.headers = {}
        monkeypatch.setattr("modules.vehicles.bmw_cardata.soc.req.get_http_session", Mock(return_value=mock_session))

        config = self._make_config(expires_at=0, container_id="test-container-id")
        result = fetch_soc(config)

        assert result.soc == 55
        assert config.configuration.access_token == "new-token"
        assert config.configuration.refresh_token == "new-refresh"

    def test_container_auto_create_when_empty(self, monkeypatch):
        call_count = [0]

        mock_get_response_empty = Mock()
        mock_get_response_empty.json.return_value = {"containers": []}

        mock_get_response_data = Mock()
        mock_get_response_data.json.return_value = {
            "telematicData": {
                "vehicle.drivetrain.electricEngine.charging.level": {"value": "60", "unit": "%"},
                "vehicle.drivetrain.electricEngine.remainingElectricRange": {"value": "290", "unit": "km"},
            }
        }

        def mock_get(url):
            call_count[0] += 1
            if "containers" in url and call_count[0] == 1:
                return mock_get_response_empty
            return mock_get_response_data

        mock_session = Mock()
        mock_session.get.side_effect = mock_get
        mock_session.post.return_value = Mock(json=Mock(return_value={"containerId": "new-container-id"}))
        mock_session.headers = {}
        monkeypatch.setattr("modules.vehicles.bmw_cardata.soc.req.get_http_session", Mock(return_value=mock_session))

        config = self._make_config(container_id="")
        result = fetch_soc(config)

        assert result.soc == 60
        assert config.configuration.container_id == "new-container-id"

    def test_container_retry_on_invalid(self, monkeypatch):
        call_count = [0]
        good_response = {
            "telematicData": {
                "vehicle.drivetrain.electricEngine.charging.level": {"value": "70", "unit": "%"},
                "vehicle.drivetrain.electricEngine.remainingElectricRange": {"value": "340", "unit": "km"},
            }
        }

        def mock_fetch(token, vin, container_id):
            call_count[0] += 1
            if call_count[0] == 1:
                mock_resp = Mock()
                mock_resp.status_code = 404
                raise RequestsHTTPError(response=mock_resp)
            return good_response

        monkeypatch.setattr("modules.vehicles.bmw_cardata.soc._fetch_telematic_data", mock_fetch)
        monkeypatch.setattr(
            "modules.vehicles.bmw_cardata.soc.get_container_id",
            Mock(return_value="new-valid-container")
        )

        result = fetch_soc(self._make_config())
        assert result.soc == 70
        assert result.range == 340

    def test_update_updates_value_store(self, monkeypatch):
        mock_response = Mock()
        mock_response.json.return_value = {
            "telematicData": {
                "vehicle.drivetrain.electricEngine.charging.level": {"value": "47", "unit": "%"},
                "vehicle.drivetrain.electricEngine.remainingElectricRange": {"value": "234", "unit": "km"},
                "vehicle.vehicle.travelledDistance": {"value": "61762", "unit": "km"},
            }
        }
        mock_session = Mock()
        mock_session.get.return_value = mock_response
        mock_session.headers = {}
        monkeypatch.setattr("modules.vehicles.bmw_cardata.soc.req.get_http_session", Mock(return_value=mock_session))

        create_vehicle(self._make_config(), 0).update(VehicleUpdateData())
        assert self.mock_value_store.set.call_count == 1
        assert self.mock_value_store.set.call_args[0][0].soc == 47
        assert self.mock_value_store.set.call_args[0][0].range == 234
        assert self.mock_value_store.set.call_args[0][0].odometer == 61762
