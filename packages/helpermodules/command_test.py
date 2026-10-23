from unittest.mock import Mock
from types import SimpleNamespace

import pytest

from control.chargepoint.chargepoint import Chargepoint
from control.chargepoint.chargepoint_state_update import ChargepointStateUpdate
from control.consumer.usage import ConsumerUsage
import dataclass_utils
from helpermodules import command
from helpermodules.command import Command
from helpermodules.measurement_logging import process_log
from helpermodules.subdata import SubData
from modules.chargepoints.external_openwb.config import OpenWBSeries
from modules.chargepoints.internal_openwb.config import (InternalOpenWB, InternalOpenWBConfiguration,
                                                         InternalChargepointMode)
from modules.chargepoints.openwb_pro.chargepoint_module import ChargepointModule as ChargepointModulePro
from modules.chargepoints.internal_openwb.chargepoint_module import ChargepointModule as ChargepointModuleInternal


pytest_plugins = ["helpermodules.measurement_logging.process_log_testdata", "helpermodules.command_test_data"]


@pytest.mark.parametrize("command_name", ["removeComponent", "removeDevice"])
@pytest.mark.parametrize("meter_id", [0, 4])
@pytest.mark.parametrize("linked_meter", [None, 0, 4, 9])
def test_remove_linked_consumer_meter(command_name, meter_id, linked_meter, monkeypatch):
    c = Command.__new__(Command)
    c.max_id_device = 2
    c.max_id_hierarchy = 10
    monkeypatch.setattr(SubData, "consumer_data", {
        "consumer8": SimpleNamespace(data=SimpleNamespace(
            extra_meter=linked_meter, module=SimpleNamespace(name="Wärmepumpe"))),
    })
    monkeypatch.setattr(SubData, "system_data", {
        "device2": SimpleNamespace(components={
            "component7": SimpleNamespace(component_config=SimpleNamespace(id=7)),
            f"component{meter_id}": SimpleNamespace(component_config=SimpleNamespace(id=meter_id)),
        }),
        "system": SimpleNamespace(data={"security": {"user_management_active": False}}),
    })
    broker_branch = Mock()
    message = Mock()
    remove_role = Mock()
    monkeypatch.setattr(command, "ProcessBrokerBranch", broker_branch)
    monkeypatch.setattr(command, "pub_user_message", message)
    monkeypatch.setattr(command, "remove_acl_role", remove_role)
    data = {"id": 2} if command_name == "removeDevice" else {
        "deviceId": 2, "id": meter_id, "type": "counter",
    }
    payload = {"data": data}

    getattr(c, command_name)("test", payload)

    if linked_meter == meter_id:
        broker_branch.assert_not_called()
        remove_role.assert_not_called()
        message.assert_called_once()
        args = message.call_args.args
        assert args[:2] == (payload, "test")
        assert args[3] == command.MessageType.ERROR
        assert "Wärmepumpe" in args[2]
        assert "separate Leistungsmessung" in args[2]
    else:
        branch = "system/device/2/" if command_name == "removeDevice" else (
            f"system/device/2/component/{meter_id}/")
        broker_branch.assert_called_once_with(branch)
        broker_branch.return_value.remove_topics.assert_called_once_with()
        assert message.call_args.args[3] == command.MessageType.SUCCESS


@pytest.fixture
def subdata_fixture() -> None:
    SubData(*([Mock()]*16))
    SubData.cp_data = {"cp0":  Mock(spec=ChargepointStateUpdate, chargepoint=Mock(
        spec=Chargepoint, chargepoint_module=Mock(spec=ChargepointModulePro)))}


@pytest.mark.parametrize(
    "additional_cp_mode, config, expected_msg",
    [
        pytest.param(None, OpenWBSeries(), None, id="Series hinzufügen"),
        pytest.param(None, InternalOpenWB(), None, id="Erste Duo hinzufügen"),
        pytest.param(InternalChargepointMode.DUO.value,
                     InternalOpenWB(),
                     None, id="Zweite Duo hinzufügen"),
        pytest.param(None, InternalOpenWB(),
                     None, id="Series hinzufügen"),
        pytest.param(InternalChargepointMode.SERIES.value,
                     InternalOpenWB(), Command.MAX_NUM_REACHED,
                     id="Zweite Series hinzufügen"),
    ]
)
def test_check_max_num_of_internal_chargepoints(additional_cp_mode, config, expected_msg, subdata_fixture, monkeypatch):
    # setup
    monkeypatch.setattr(Command, "_get_max_ids", Mock())
    monkeypatch.setattr(Command, "_get_max_id_hierarchy_by_topics", Mock())
    if additional_cp_mode:
        SubData.cp_data.update(
            {"cp1": Mock(spec=ChargepointStateUpdate, chargepoint=Mock(
                spec=Chargepoint, chargepoint_module=Mock(spec=ChargepointModuleInternal, config=InternalOpenWB(
                    configuration=InternalOpenWBConfiguration(mode=additional_cp_mode)))))})

    # execution
    msg = Command(Mock())._check_max_num_of_internal_chargepoints(dataclass_utils.asdict(config))

    # evaluation
    assert msg == expected_msg


def test_getDailyLog(regular_daily_log_entry,
                     regular_daily_log_entry_processed_legacy_converted,
                     mock_pub,
                     monkeypatch):
    # setup
    c = Command(Mock())
    mock_pub.reset_mock()
    collect_daily_log_data_mock = Mock(return_value=regular_daily_log_entry)
    monkeypatch.setattr(process_log, "_collect_daily_log_data", collect_daily_log_data_mock)

    # execution
    c.getDailyLog("test", {"data": {"date": "20250616"}})

    # evaluation
    assert len(mock_pub.method_calls) == 1
    assert mock_pub.method_calls[0][1][0] == 'openWB/set/log/daily/20250616'
    assert mock_pub.method_calls[0][1][1] == regular_daily_log_entry_processed_legacy_converted


@pytest.mark.parametrize("usage_type", [ConsumerUsage.SUSPENDABLE_TUNABLE, ConsumerUsage.METER_ONLY])
def test_add_consumer_uses_module_default_usage_type(usage_type, mock_pub, monkeypatch):
    consumer_setup = SimpleNamespace(
        id=0,
        type="test_consumer",
        name="Test-Verbraucher",
        info={},
        configuration=SimpleNamespace(),
        vendor="test",
        usage=(usage_type,),
    )
    descriptor = SimpleNamespace(configuration_factory=Mock(return_value=consumer_setup))
    monkeypatch.setattr(command.importlib, "import_module", Mock(return_value=SimpleNamespace(
        device_descriptor=descriptor)))
    monkeypatch.setattr(command, "pub_user_message", Mock())
    monkeypatch.setattr(SubData, "counter_all_data", Mock())
    SubData.counter_all_data.get_id_evu_counter.return_value = 0
    SubData.counter_all_data.data.get.hierarchy = []
    SubData.counter_all_data.data.get.loadmanagement_prios = []
    command_instance = Command.__new__(Command)
    command_instance.max_id_hierarchy = 0

    command_instance.addConsumer("test", {"data": {"vendor": "test", "type": "test_consumer"}})

    usage_calls = [call for call in mock_pub.pub.call_args_list
                   if call.args[0] == "openWB/consumer/1/usage"]
    assert len(usage_calls) == 1
    assert usage_calls[0].args[1]["type"] == usage_type.value


def test_get_max_id_hierarchy_by_topics(mock_pub, monkeypatch):
    command_instance = Command.__new__(Command)
    command_instance._get_max_id_hierarchy_by_topics({
        "openWB/counter/4/get/power": 500,
        "openWB/chargepoint/9/config": {"id": 9},
        "openWB/consumer/5/module": {"type": "dummy"},
    }, -1)

    assert command_instance.max_id_hierarchy == 9
    mock_pub.pub.assert_any_call("openWB/set/command/max_id/hierarchy", 9)


@pytest.mark.parametrize("consumer_type", ["internal_socket", "mqtt"])
def test_remove_internal_socket_switches_off_before_removing_topics(consumer_type, mock_pub, monkeypatch):
    order = []
    consumer = SimpleNamespace(data=SimpleNamespace(module=SimpleNamespace(type=consumer_type)), module=Mock())
    consumer.module.switch_off.side_effect = lambda: order.append("off")
    branch = Mock()
    branch.remove_topics.side_effect = lambda: order.append("remove")
    monkeypatch.setattr(command, "ProcessBrokerBranch", Mock(return_value=branch))
    monkeypatch.setattr(command, "pub_user_message", Mock())
    monkeypatch.setattr(SubData, "consumer_data", {"consumer2": consumer})
    monkeypatch.setattr(SubData, "counter_all_data", Mock())
    monkeypatch.setattr(SubData, "system_data", {
        "system": SimpleNamespace(data={"security": {"user_management_active": False}})})
    instance = Command.__new__(Command)
    instance.max_id_hierarchy = 2
    instance.removeConsumer("test", {"data": {"consumer_id": 2}})
    assert order == (["off", "remove"] if consumer_type == "internal_socket" else ["remove"])


@pytest.mark.parametrize("existing_type, requested_type, existing_cp, requested_cp, blocked", [
    ("internal_socket", "internal_socket", None, None, True),
    ("mqtt", "internal_socket", None, None, False),
    (None, "internal_socket", None, None, False),
    ("internal_socket", "mqtt", None, None, False),
    ("internal_socket", "internal_socket", None, 4, False),
    ("internal_socket", "internal_socket", 4, None, False),
    ("internal_socket", "internal_socket", 4, 5, False),
    ("internal_socket", "internal_socket", 4, 4, True),
    ("internal_socket", "internal_socket", 4, 6, True),
    ("internal_socket", "internal_socket", None, 0, True),
    ("internal_socket", "internal_socket", 0, None, True),
])
def test_add_consumer_rejects_second_internal_socket_before_side_effects(
        existing_type, requested_type, existing_cp, requested_cp, blocked, mock_pub, monkeypatch):
    existing_module = SimpleNamespace(type=existing_type, configuration=SimpleNamespace(
        chargepoint_id=existing_cp)) if existing_type else None
    monkeypatch.setattr(SubData, "consumer_data", {
        "consumer2": SimpleNamespace(num=2, data=SimpleNamespace(module=existing_module))})
    monkeypatch.setattr(SubData, "cp_data", {
        f"cp{num}": SimpleNamespace(chargepoint=SimpleNamespace(chargepoint_module=SimpleNamespace(
            config=SimpleNamespace(type="external_openwb", configuration=SimpleNamespace(ip_address=host)))))
        for num, host in [(4, "192.168.1.40"), (5, "192.168.1.50"), (6, "192.168.1.40")]})
    SubData.cp_data["cp0"] = SimpleNamespace(chargepoint=SimpleNamespace(chargepoint_module=SimpleNamespace(
        config=SimpleNamespace(type="internal_openwb"))))
    counter = Mock()
    counter.get_id_evu_counter.return_value = 0
    counter.data.get.hierarchy = []
    counter.data.get.loadmanagement_prios = []
    monkeypatch.setattr(SubData, "counter_all_data", counter)
    monkeypatch.setattr(SubData, "system_data", {
        "system": SimpleNamespace(data={"security": {"user_management_active": False}})})
    message = Mock()
    monkeypatch.setattr(command, "pub_user_message", message)
    vendor = "openwb" if requested_type == "internal_socket" else "generic"
    setup = SimpleNamespace(id=0, type=requested_type, name="Test-Verbraucher", info={},
                            configuration=SimpleNamespace(), vendor=vendor,
                            usage=(ConsumerUsage.SUSPENDABLE_ONOFF,))
    module_import = Mock(return_value=SimpleNamespace(device_descriptor=SimpleNamespace(
        configuration_factory=Mock(return_value=setup))))
    monkeypatch.setattr(command.importlib, "import_module", module_import)
    instance = Command.__new__(Command)
    instance.max_id_hierarchy = 2
    payload = {"data": {"vendor": vendor, "type": requested_type,
                        "configuration": {"chargepoint_id": requested_cp}}}

    instance.addConsumer("test", payload)

    if blocked:
        message.assert_called_once_with(
            payload, "test", "Die Steckdose dieser openWB kann nur einem Verbraucher zugeordnet werden.",
            command.MessageType.ERROR)
        module_import.assert_not_called()
        counter.get_id_evu_counter.assert_not_called()
        counter.hierarchy_add_item_below.assert_not_called()
        counter.add_loadmanagement_prio_item.assert_not_called()
        mock_pub.pub.assert_not_called()
        assert instance.max_id_hierarchy == 2
    else:
        assert instance.max_id_hierarchy == 3
        counter.hierarchy_add_item_below.assert_called_once()
        assert any(call.args[0] == "openWB/consumer/3/module" for call in mock_pub.pub.call_args_list)
        if requested_type == "internal_socket":
            module_payload = next(call.args[1] for call in mock_pub.pub.call_args_list
                                  if call.args[0] == "openWB/consumer/3/module")
            assert module_payload["configuration"] == {"chargepoint_id": requested_cp}
