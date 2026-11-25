from unittest.mock import Mock

import pytest

from control import data
from modules.chargepoints.external_openwb import chargepoint_module
from modules.chargepoints.external_openwb.chargepoint_module import ChargepointModule, REQUIRED_TOPICS
from modules.chargepoints.external_openwb.config import OpenWBSeries, OpenWBSeriesConfiguration

PREFIX = "openWB/internal_chargepoint/1/get/"
RECEIVED = {f"{PREFIX}power": 1500, f"{PREFIX}phases_in_use": 1, f"{PREFIX}imported": 1000,
            f"{PREFIX}exported": 0, f"{PREFIX}currents": [6.5, 0, 0], f"{PREFIX}plug_state": True,
            f"{PREFIX}charge_state": True}


@pytest.fixture
def module(monkeypatch) -> ChargepointModule:
    monkeypatch.setattr(chargepoint_module, "get_chargepoint_value_store", Mock())
    system = Mock(data={"ip_address": "10.0.0.2"})
    monkeypatch.setattr(data, "data", Mock(system_data={"system": system}), raising=False)
    return ChargepointModule(OpenWBSeries(id=5, configuration=OpenWBSeriesConfiguration("10.0.0.5", duo_num=1)))


def test_get_values_publishes_bundled_and_collects_over_one_connection(module, monkeypatch):
    collect = Mock(return_value=RECEIVED)
    pub_single = Mock()
    pub_multiple = Mock()
    monkeypatch.setattr(chargepoint_module, "publish_and_collect", collect)
    monkeypatch.setattr(chargepoint_module.pub, "pub_single", pub_single)
    monkeypatch.setattr(chargepoint_module.pub, "pub_multiple", pub_multiple)

    module.get_values()

    pub_single.assert_not_called()
    pub_multiple.assert_not_called()
    args = collect.call_args.args
    assert args[:2] == ("10.0.0.5", 1883)
    assert [(m["topic"], m["payload"]) for m in args[2]] == [
        ("openWB/set/internal_chargepoint/global_data", '{"heartbeat": 1652683252, "parent_ip": "10.0.0.2"}'),
        ("openWB/set/isss/heartbeat", "0"),
        ("openWB/set/isss/parentWB", "10.0.0.2"),
        ("openWB/set/internal_chargepoint/1/data/parent_cp", '"5"'),
        ("openWB/set/isss/parentCPlp2", '"5"')]
    assert args[3] == f"{PREFIX}#"
    assert collect.call_args.kwargs == {"name": "subscribeSeriesChargepoint5"}
    state = module.store.set.call_args.args[0]
    assert state.power == 1500
    assert state.currents == [6.5, 0, 0]


def test_get_values_uses_internal_broker_port_for_localhost(module, monkeypatch):
    collect = Mock(return_value=RECEIVED)
    monkeypatch.setattr(chargepoint_module, "publish_and_collect", collect)
    module.config.configuration.ip_address = "localhost"

    module.get_values()

    assert collect.call_args.args[:2] == ("localhost", 1886)


def test_data_is_complete_when_all_required_topics_are_received(module, monkeypatch):
    collect = Mock(return_value=RECEIVED)
    monkeypatch.setattr(chargepoint_module, "publish_and_collect", collect)
    module.get_values()
    is_complete = collect.call_args.args[4]

    assert is_complete(RECEIVED) is True
    assert is_complete({}) is False
    for topic in REQUIRED_TOPICS:
        assert is_complete({k: v for k, v in RECEIVED.items() if k != f"{PREFIX}{topic}"}) is False
    # Topics eines anderen Ladepunkts am selben Secondary zählen nicht
    assert is_complete({k.replace("/1/", "/0/"): v for k, v in RECEIVED.items()}) is False


def test_get_values_warns_when_nothing_was_received(module, monkeypatch):
    monkeypatch.setattr(chargepoint_module, "publish_and_collect", Mock(return_value={}))
    warning = Mock()
    monkeypatch.setattr(module.fault_state, "warning", warning)

    module.get_values()

    module.store.set.assert_not_called()
    assert "Keine MQTT-Daten" in warning.call_args.args[0]


def test_get_values_reports_fault_of_remote_chargepoint_when_required_data_is_missing(module, monkeypatch, caplog):
    received = {f"{PREFIX}fault_state": 2, f"{PREFIX}fault_str": "Fehler am Secondary"}
    monkeypatch.setattr(chargepoint_module, "publish_and_collect", Mock(return_value=received))

    module.get_values()

    module.store.set.assert_not_called()
    assert "Fehler am Secondary" in caplog.text


def test_set_current_publishes_both_topics_over_one_connection(module, monkeypatch):
    pub_multiple = Mock()
    monkeypatch.setattr(chargepoint_module.pub, "pub_multiple", pub_multiple)

    module.set_current(10)

    pub_multiple.assert_called_once()
    messages = pub_multiple.call_args.args[0]
    assert [(m.topic, m.payload) for m in messages] == [
        ("openWB/set/internal_chargepoint/1/data/set_current", 10),
        ("openWB/set/isss/Lp2Current", 10)]
    assert pub_multiple.call_args.kwargs == {"hostname": "10.0.0.5"}


def test_switch_phases_publishes_over_one_connection(module, monkeypatch):
    pub_multiple = Mock()
    monkeypatch.setattr(chargepoint_module.pub, "pub_multiple", pub_multiple)

    module.switch_phases(3)

    messages = pub_multiple.call_args.args[0]
    assert [(m.topic, m.payload) for m in messages] == [
        ("openWB/set/internal_chargepoint/1/data/phases_to_use", 3),
        ("openWB/set/internal_chargepoint/1/data/trigger_phase_switch", True),
        ("openWB/set/isss/U1p3p", 3)]
    assert pub_multiple.call_args.kwargs == {"hostname": "10.0.0.5"}


def test_connection_error_of_set_current_is_counted_as_client_error(module, monkeypatch):
    monkeypatch.setattr(chargepoint_module.pub, "pub_multiple", Mock(side_effect=ConnectionError(113, "x")))

    module.set_current(10)

    assert module.client_error_context.error_timestamp is not None
