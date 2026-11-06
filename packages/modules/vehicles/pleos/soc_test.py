from unittest.mock import Mock

import pytest

from modules.common import store
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.component_context import SingleComponentUpdateContext
from modules.vehicles.pleos import api
from modules.vehicles.pleos.soc import create_vehicle
from modules.vehicles.pleos.config import Pleos, PleosConfiguration, PleosToken


class TestPleos:
    @pytest.fixture(autouse=True)
    def set_up(self, monkeypatch):
        self.token = PleosToken(access_token="tok")
        self.mock_context_exit = Mock(return_value=True)
        self.mock_value_store = Mock(name="value_store")
        monkeypatch.setattr(api, "validate_token", Mock(return_value=self.token))
        monkeypatch.setattr(api, "get_battery", Mock(return_value={
            "charge": {"stateOfCharge": 72.5, "targetStateOfCharge": {"standard": 100}},
            "timestamp": "2026-10-02T13:51:37Z"}))
        monkeypatch.setattr(api, "get_distance_to_empty_km", Mock(return_value=210.0))
        monkeypatch.setattr(api, "get_odometer_km", Mock(return_value=15234.0))
        monkeypatch.setattr(store, "get_car_value_store", Mock(return_value=self.mock_value_store))
        monkeypatch.setattr(SingleComponentUpdateContext, '__exit__', self.mock_context_exit)

    def _vehicle(self, vin="VIN1"):
        return create_vehicle(Pleos(configuration=PleosConfiguration(
            brand="kia", client_id="cid", client_secret="csec", vin=vin, token=self.token)), 0)

    def test_update_updates_value_store(self):
        self._vehicle().update(VehicleUpdateData())

        assert self.mock_context_exit.call_args[0][1] is None
        assert self.mock_value_store.set.call_count == 1
        result = self.mock_value_store.set.call_args[0][0]
        assert result.soc == 72.5
        assert result.range == 210.0
        assert result.odometer == 15234.0
        assert result.soc_timestamp == 1790949097.0
        assert result.warning is None

    def test_target_soc_below_100_sets_warning(self):
        api.get_battery.return_value = {"charge": {"stateOfCharge": 50, "targetStateOfCharge": {"standard": 80}}}

        self._vehicle().update(VehicleUpdateData())

        assert self.mock_value_store.set.call_args[0][0].warning == \
            "Das Fahrzeug begrenzt die Ladung selbst auf 80%."

    def test_raises_when_vin_not_configured(self):
        self._vehicle(vin=None).update(VehicleUpdateData())

        assert "VIN" in str(self.mock_context_exit.call_args[0][1])
        api.get_battery.assert_not_called()

    def test_update_passes_errors_to_context(self):
        dummy_error = Exception("Pleos: Token-Anfrage fehlgeschlagen")
        api.validate_token.side_effect = dummy_error

        self._vehicle().update(VehicleUpdateData())

        assert str(dummy_error) in str(self.mock_context_exit.call_args[0][1])
