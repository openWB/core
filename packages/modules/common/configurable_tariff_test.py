from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from helpermodules import timecheck
import pytest

from modules.common.component_state import TariffState
from modules.common.configurable_tariff import ConfigurableElectricityTariff
from modules.electricity_tariffs.awattar.config import AwattarTariff


class DummyConfig:
    name = "TestTariff"


class DummyTariffState:
    def __init__(self, prices):
        self.prices = prices


def dummy_component_initializer(config):
    def updater():
        now = int(datetime.now().timestamp())
        return DummyTariffState({str(now + 3600): 1.0, str(now + 7200): 2.0})

    return updater


@pytest.mark.parametrize(
    "tariff_state_factory, last_known_timestamp, expected_log_method, expected_log_call",
    [
        pytest.param(
            lambda: DummyTariffState(
                {
                    str(int(datetime.now().timestamp()) + 3600): 1.0,
                    str(int(datetime.now().timestamp()) + 7200): 2.0,
                }
            ),
            lambda: "0",
            "info",
            True,
            id="success_new_data_info_log",
        ),
        pytest.param(
            lambda: DummyTariffState(
                {str(int(datetime.now().timestamp()) + 7200): 1.0}
            ),
            lambda: str(int(datetime.now().timestamp()) + 7200),
            "info",
            True,
            id="no_new_data_info_log",
        ),
        pytest.param(
            lambda: (_ for _ in ()).throw(Exception("Test error")),
            lambda: "0",
            "warning",
            True,
            id="exception_warning_log",
        ),
        pytest.param(
            lambda: DummyTariffState({}),
            lambda: "0",
            "warning",
            True,
            id="empty response_warning_log",
        ),
    ],
)
def test_query_et_provider_data_once_per_day_param(
    monkeypatch,
    tariff_state_factory,
    last_known_timestamp,
    expected_log_method,
    expected_log_call,
):
    config = DummyConfig()
    # For exception case, use a special component_initializer
    if expected_log_method == "warning":

        def failing_component_initializer(config):
            def updater():
                raise Exception("Test error")

            return updater

        tariff = ConfigurableElectricityTariff(config, failing_component_initializer)
    else:

        def component_initializer(config):
            return lambda: tariff_state_factory()

        tariff = ConfigurableElectricityTariff(config, component_initializer)
    tariff._ConfigurableElectricityTariff__next_query_time = datetime.now() - timedelta(
        days=1
    )
    tariff._ConfigurableElectricityTariff__tariff_state = DummyTariffState(
        {str(int(datetime.now().timestamp())): 1.0}
    )
    monkeypatch.setattr(
        tariff,
        "_ConfigurableElectricityTariff__get_last_entry_time_stamp",
        last_known_timestamp,
    )
    monkeypatch.setattr(
        tariff, "_ConfigurableElectricityTariff__calulate_next_query_time", lambda: None
    )
    with patch("modules.common.configurable_tariff.log") as mock_log:
        tariff._ConfigurableElectricityTariff__query_et_provider_data_once_per_day()
        assert getattr(mock_log, expected_log_method).called == expected_log_call


@pytest.mark.parametrize(
    "now, tariff_state, expected",
    [
        pytest.param(
            1652680800,
            TariffState(
                prices={
                    "1652680800": -5.87e-06,
                    "1652684400": 5.467e-05,
                    "1652688000": 10.72e-05,
                }
            ),
            TariffState(
                prices={
                    "1652680800": -5.87e-06,
                    "1652684400": 5.467e-05,
                    "1652688000": 10.72e-05,
                }
            ),
            id="keine veralteten Einträge",
        ),
        pytest.param(
            1652680800,
            TariffState(
                prices={
                    "1652677200": -5.87e-06,
                    "1652680800": 5.467e-05,
                    "1652684400": 10.72e-05,
                }
            ),
            TariffState(prices={"1652680800": 5.467e-05, "1652684400": 10.72e-05}),
            id="Lösche ersten Eintrag",
        ),
        pytest.param(
            1652684000,
            TariffState(
                prices={
                    "1652680800": -5.87e-06,
                    "1652684400": 5.467e-05,
                    "1652688000": 10.72e-05,
                }
            ),
            TariffState(
                prices={
                    "1652680800": -5.87e-06,
                    "1652684400": 5.467e-05,
                    "1652688000": 10.72e-05,
                }
            ),
            id="erster time slot noch nicht zu Ende",
        ),
        pytest.param(
            1652684000,
            TariffState(
                prices={
                    "1652680000": -5.87e-06,
                    "1652681200": 5.467e-05,
                    "1652682400": 10.72e-05,
                    "1652683600": 10.72e-05,
                    "1652684800": 10.72e-05,
                    "1652686000": 10.72e-05,
                    "1652687200": 10.72e-05,
                }
            ),
            TariffState(
                prices={
                    "1652683600": 10.72e-05,
                    "1652684800": 10.72e-05,
                    "1652686000": 10.72e-05,
                    "1652687200": 10.72e-05,
                }
            ),
            id="20 Minuten time slots",
        ),
    ],
)
def test_remove_outdated_prices(
    now: int, tariff_state: TariffState, expected: TariffState, monkeypatch
):
    # setup
    tariff = ConfigurableElectricityTariff(AwattarTariff(), Mock())
    time_slot_seconds = [int(timestamp) for timestamp in tariff_state.prices.keys()][:2]

    # Montag 16.05.2022, 8:40:52  "05/16/2022, 08:40:52" Unix: 1652683252
    monkeypatch.setattr(timecheck, "create_timestamp", Mock(return_value=now))

    # test
    result = tariff._remove_outdated_prices(
        tariff_state, time_slot_seconds[1] - time_slot_seconds[0]
    )

    # assert
    assert result.prices == expected.prices


def test_accept_no_prices_at_start(monkeypatch):
    # setup
    tariff = ConfigurableElectricityTariff(
        AwattarTariff(),
        Mock(
            return_value=TariffState(
                prices={"5": 10.72e-05, "6": 10.72e-05, "7": 10.72e-05, "8": 10.72e-05}
            )
        ),
    )

    # Montag 16.05.2022, 8:40:52  "05/16/2022, 08:40:52" Unix: 1652683252
    monkeypatch.setattr(timecheck, "create_timestamp", Mock(return_value=5))

    # test - do not fail
    tariff._remove_outdated_prices(TariffState(), 1)
