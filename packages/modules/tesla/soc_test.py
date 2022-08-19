from unittest.mock import Mock

import pytest

from modules.common import store
from modules.common.component_context import SingleComponentUpdateContext
from modules.tesla import api
from modules.tesla.soc import Soc
from modules.tesla.config import TeslaSoc, TeslaSocConfiguration, TeslaSocToken


class TestTesla:
    @pytest.fixture(autouse=True)
    def set_up(self, monkeypatch):
        self.token = TeslaSocToken()
        self.mock_context_exit = Mock(return_value=True)
        self.mock_validate_token = Mock(name="validate_token", return_value=self.token)
        self.mock_post_wake_up_command = Mock(name="post_wake_up_command", return_value="online")
        self.mock_request_soc_range = Mock(name="request_soc_range", return_value=(42.5, 438.2))
        self.mock_value_store = Mock(name="value_store")
        monkeypatch.setattr(api, "validate_token", self.mock_validate_token)
        monkeypatch.setattr(api, "post_wake_up_command", self.mock_post_wake_up_command)
        monkeypatch.setattr(api, "request_soc_range", self.mock_request_soc_range)
        monkeypatch.setattr(store, "get_car_value_store", Mock(return_value=self.mock_value_store))
        monkeypatch.setattr(SingleComponentUpdateContext, '__exit__', self.mock_context_exit)

    def test_update_updates_value_store_no_chargepoint(self, monkeypatch):
        # execution
        Soc(TeslaSoc(configuration=TeslaSocConfiguration(
            tesla_ev_num=0, token=self.token)), 0).update(False)

        # evaluation
        self.assert_context_manager_called_with(None)
        self.mock_request_soc_range.assert_called_once_with(vehicle=0, token=self.token)
        assert self.mock_value_store.set.call_count == 1
        assert self.mock_value_store.set.call_args[0][0].soc == 42.5
        assert self.mock_value_store.set.call_args[0][0].range == 438.2

    def test_update_updates_value_store_not_charging(self, monkeypatch):
        # execution
        Soc(TeslaSoc(configuration=TeslaSocConfiguration(
            tesla_ev_num=0, token=self.token)), 0).update(False)

        # evaluation
        self.assert_context_manager_called_with(None)
        self.mock_request_soc_range.assert_called_once_with(vehicle=0, token=self.token)

        assert self.mock_value_store.set.call_count == 1
        assert self.mock_value_store.set.call_args[0][0].soc == 42.5

    def test_update_passes_errors_to_context(self, monkeypatch):
        # setup
        dummy_error = Exception()
        self.mock_request_soc_range.side_effect = dummy_error

        # execution
        Soc(TeslaSoc(configuration=TeslaSocConfiguration(
            tesla_ev_num=0, token=self.token)), 0).update(False)

        # evaluation
        self.assert_context_manager_called_with(dummy_error)

    def assert_context_manager_called_with(self, error):
        assert self.mock_context_exit.call_count == 1
        assert self.mock_context_exit.call_args[0][1] is error
