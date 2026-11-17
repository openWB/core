import asyncio
import concurrent.futures
import copy
import json
from types import MethodType, SimpleNamespace

from control import prepare
from control.chargepoint import chargepoint as chargepoint_module
from control.chargepoint import rfid

from typing import Optional
from unittest.mock import AsyncMock, Mock

import pytest
from control import data
from control.chargepoint.chargepoint import Chargepoint
from control.chargepoint.chargepoint_template import CpTemplate
from control.ev.ev import Ev
from control.ocpp import ocpp_chargepoint
from control.ocpp.ocpp_chargepoint import OcppChargePoint
from control.ocpp.ocpp_client import OcppClient
from helpermodules.subdata import SubData
from helpermodules import setdata
from modules.common.component_state import ChargepointState
from modules.common.store import _chargepoint as chargepoint_store
from ocpp.v16.enums import RemoteStartStopStatus


@pytest.mark.parametrize("processing_index", [0, 1])
def test_duo_rejected_scan_remains_blocked_after_reconnecting(duo, rfid_tag, processing_index):
    cp = duo.chargepoints[processing_index]
    partner = duo.chargepoints[1 - processing_index]
    timestamp = duo.clock.return_value
    for point, tag in zip((cp, partner), (rfid_tag, "ABC")):
        point.data.get.plug_state = True
        point.data.set.rfid = tag
        point.data.set.rfid_timestamp = timestamp - 10
    for point in duo.chargepoints:
        point.template.data.valid_tags.append("C")

    duo.reader.scan("C", timestamp)
    cp._validate_rfid()

    assert cp.data.set.rfid == rfid_tag
    assert partner.data.set.rfid == "ABC"
    assert cp.data.set.rfid_timestamp == timestamp
    assert partner.data.set.rfid_timestamp == timestamp - 10
    assert all(point.data.get.rfid is None for point in duo.chargepoints)
    cp.chargepoint_module.clear_rfid.assert_called_once_with()

    # Der Partner ist nach Ab-/Wiederanstecken wieder unzugeordnet.
    partner.data.set.rfid = None
    partner.data.set.manual_lock = True
    partner.data.get.plug_state = True
    duo.clock.return_value += 600
    partner.data.set.plug_time = duo.clock.return_value
    duo.reader.scan("C", timestamp)
    partner._validate_rfid()
    cp._validate_rfid()

    assert partner.data.set.rfid is None
    assert partner.data.set.manual_lock is True
    assert all(point.data.get.rfid is None for point in duo.chargepoints)
    assert cp.data.set.rfid == rfid_tag

    # Ein echter neuer Scan derselben Karte darf weiterhin zugeordnet werden.
    duo.clock.return_value += 1
    duo.reader.scan("C", duo.clock.return_value)
    partner._validate_rfid()
    partner._link_rfid_to_cp()
    assert partner.data.set.rfid == "C"
    assert partner.data.set.rfid_timestamp == duo.clock.return_value
    assert cp.data.set.rfid == rfid_tag


def test_acknowledgement_does_not_decrease_processed_timestamp(duo, rfid_tag):
    cp, partner = duo.chargepoints
    timestamp = duo.clock.return_value
    cp.data.set.rfid_timestamp = timestamp + 10
    duo.reader.scan(rfid_tag, timestamp)

    cp._clear_pending_rfid(rfid_tag, partner, timestamp)

    assert cp.data.set.rfid_timestamp == timestamp + 10


@pytest.mark.parametrize("same_card", [False, True])
def test_acknowledging_scan_preserves_newer_scan_at_partner(duo, rfid_tag, same_card):
    cp, partner = duo.chargepoints
    timestamp = duo.clock.return_value
    cp.data.get.rfid = rfid_tag
    cp.data.get.rfid_timestamp = timestamp
    newer_tag = rfid_tag if same_card else "ABC"
    partner.data.get.rfid = newer_tag
    partner.data.get.rfid_timestamp = timestamp + 1

    cp._clear_pending_rfid(rfid_tag, partner, timestamp)

    assert cp.data.get.rfid is None
    assert cp.data.get.rfid_timestamp is None
    assert partner.data.get.rfid == newer_tag
    assert partner.data.get.rfid_timestamp == timestamp + 1
    assert all(point.chargepoint_module.clear_rfid.call_count == 0 for point in duo.chargepoints)


@pytest.mark.parametrize("selected_index", [0, 1])
@pytest.mark.parametrize("reverse_order", [False, True])
@pytest.mark.parametrize("replay_offset", [0, -1], ids=["Gleicher-Scan", "Aelterer-Scan"])
def test_duo_reader_timestamp_prevents_second_authorization(
        duo, rfid_tag, selected_index, reverse_order, replay_offset, mock_pub):
    from helpermodules.changed_values_handler import ChangedValuesHandler

    selected = duo.chargepoints[selected_index]
    other = duo.chargepoints[1 - selected_index]
    order = list(reversed(duo.chargepoints)) if reverse_order else duo.chargepoints
    selected.data.get.plug_state = True
    selected.data.set.plug_time = duo.clock.return_value - 10
    scanned_at = duo.clock.return_value - 2

    def process():
        for cp in order:
            cp._validate_rfid()
            if cp.data.get.rfid is not None and cp.data.get.plug_state:
                cp._link_rfid_to_cp()
            cp.is_charging_possible()

    previous_set = copy.deepcopy(selected.data.set)
    duo.reader.scan(rfid_tag, scanned_at)
    process()
    assert selected.data.set.rfid == rfid_tag
    assert selected.data.set.rfid_timestamp == scanned_at
    # Beide Felder werden gemeinsam über den bestehenden Änderungs-Handler veröffentlicht.
    handler = object.__new__(ChangedValuesHandler)
    handler._update_value(f"openWB/set/chargepoint/{selected.num}/", previous_set, selected.data.set)
    mock_pub.pub.assert_any_call(f"openWB/set/chargepoint/{selected.num}/set/rfid", rfid_tag)
    mock_pub.pub.assert_any_call(f"openWB/set/chargepoint/{selected.num}/set/rfid_timestamp", scanned_at)

    # Wie im Fehlerlog: nach der Quittierung trifft der alte Scan erneut ein.
    duo.clock.return_value += 10
    duo.reader.scan(rfid_tag, scanned_at + replay_offset)
    process()
    assert all(cp.data.get.rfid is None for cp in duo.chargepoints)
    assert all(cp.data.get.rfid_timestamp is None for cp in duo.chargepoints)
    assert other.data.set.rfid is None
    assert other.data.set.manual_lock is True
    assert sum(cp.chargepoint_module.clear_rfid.call_count for cp in duo.chargepoints) == 1

    other.data.get.plug_state = True
    other.data.set.plug_time = duo.clock.return_value
    process()
    assert other.data.set.rfid is None
    assert other.data.set.manual_lock is True

    # Erst ein echter neuer Scan derselben Karte gibt den anderen LP frei.
    duo.clock.return_value += 1
    duo.reader.scan(rfid_tag, duo.clock.return_value)
    process()
    assert other.data.set.rfid == rfid_tag
    assert other.data.set.rfid_timestamp == duo.clock.return_value
    assert selected.data.set.rfid_timestamp == scanned_at
    assert sum(cp.chargepoint_module.clear_rfid.call_count for cp in duo.chargepoints) == 2


@pytest.mark.parametrize("new_first", [False, True])
def test_duo_old_replay_does_not_clear_newer_scan_at_partner(duo, rfid_tag, new_first):
    cp, partner = duo.chargepoints
    cp.data.set.rfid_timestamp = duo.clock.return_value - 10
    cp.data.get.rfid = rfid_tag
    cp.data.get.rfid_timestamp = cp.data.set.rfid_timestamp
    partner.data.get.rfid = rfid_tag
    partner.data.get.rfid_timestamp = duo.clock.return_value

    (partner if new_first else cp)._validate_rfid()

    # Bei Verarbeitung des neuen Scans darf dieser an beiden leeren LP warten.
    assert cp.data.get.rfid == (rfid_tag if new_first else None)
    assert cp.data.get.rfid_timestamp == (duo.clock.return_value if new_first else None)
    assert partner.data.get.rfid == rfid_tag
    assert partner.data.get.rfid_timestamp == duo.clock.return_value
    assert all(point.chargepoint_module.clear_rfid.call_count == 0 for point in duo.chargepoints)


@pytest.mark.parametrize("duo_mode", [False, True], ids=["Einzel-LP", "Duo"])
def test_legacy_reader_without_timestamp_remains_supported(duo, rfid_tag, duo_mode):
    cp, partner = duo.chargepoints
    if not duo_mode:
        data.data.cp_data.pop(f"cp{partner.num}")
    cp.data.set.rfid_timestamp = duo.clock.return_value - 100
    cp.data.get.plug_state = True
    cp.data.set.plug_time = duo.clock.return_value - 10
    duo.reader.scan(rfid_tag)

    cp._validate_rfid()
    assert cp.data.get.rfid_timestamp == duo.clock.return_value
    cp._link_rfid_to_cp()

    assert cp.data.set.rfid == rfid_tag
    assert cp.data.set.rfid_timestamp == duo.clock.return_value


@pytest.mark.parametrize("duo_mode", [False, True], ids=["Einzel-LP", "Duo"])
def test_reader_timestamp_starts_timeout_at_scan_time(duo, rfid_tag, duo_mode):
    cp, partner = duo.chargepoints
    if not duo_mode:
        data.data.cp_data.pop(f"cp{partner.num}")
    scanned_at = duo.clock.return_value - 299
    duo.reader.scan(rfid_tag, scanned_at)
    cp._validate_rfid()
    assert cp.data.get.rfid_timestamp == scanned_at
    duo.clock.return_value += 2
    cp._validate_rfid()
    assert cp.data.get.rfid is None
    assert "verworfen" in cp.data.get.state_str


def test_reader_generates_new_timestamp_for_each_scan(duo, monkeypatch):
    import asyncio
    from modules.internal_chargepoint_handler import rfid as reader_module

    async def events():
        # Zweimal dieselbe Karte, jeweils mit Enter abgeschlossen.
        for scancode in (reader_module.ecodes.KEY_1, reader_module.ecodes.KEY_ENTER) * 2:
            yield SimpleNamespace(type=reader_module.ecodes.EV_KEY, keystate=1, scancode=scancode)

    monkeypatch.setattr(reader_module, "categorize", lambda event: event)
    monkeypatch.setattr(reader_module, "Pub", Mock(return_value=duo.mqtt))
    duo.clock.side_effect = [1_700_000_000.125, 1_700_000_001.25]
    reader = object.__new__(reader_module.RfidReader)
    device = SimpleNamespace(path="test-reader", async_read_loop=events)

    asyncio.run(reader._read_events(device))

    assert [call.args for call in duo.mqtt.pub.call_args_list] == [
        ("openWB/set/internal_chargepoint/last_tag_timestamp", 1_700_000_000.125),
        ("openWB/set/internal_chargepoint/last_tag", "1"),
        ("openWB/set/internal_chargepoint/last_tag_timestamp", 1_700_000_001.25),
        ("openWB/set/internal_chargepoint/last_tag", "1"),
    ]


def test_scan_timestamp_topics_are_validated_and_applied(duo, mock_pub, monkeypatch):
    import json
    from helpermodules.setdata import SetData
    from helpermodules.subdata import SubData
    from modules.internal_chargepoint_handler.internal_chargepoint_handler_config import RfidData

    cp = duo.chargepoints[0]
    monkeypatch.setattr(SubData, "cp_data", {f"cp{cp.num}": SimpleNamespace(chargepoint=cp)})
    setter = object.__new__(SetData)
    subscriber = object.__new__(SubData)
    reader_data = RfidData()
    timestamp = duo.clock.return_value + 0.125
    for topic, target, attribute, process in (
            ("openWB/set/internal_chargepoint/last_tag_timestamp", reader_data,
             "last_tag_timestamp", setter.process_internal_chargepoint_topic),
            (f"openWB/set/chargepoint/{cp.num}/set/rfid_timestamp", cp.data.set,
             "rfid_timestamp", setter.process_chargepoint_topic)):
        for value in (timestamp, None):
            message = SimpleNamespace(topic=topic, payload=json.dumps(value).encode())
            process(message)
            published_topic = topic.replace("set/", "", 1)
            mock_pub.pub.assert_any_call(published_topic, value, retain=True)
            subscriber.set_json_payload_class(target, SimpleNamespace(
                topic=published_topic, payload=message.payload))
            assert getattr(target, attribute) == value


def test_internal_chargepoint_forwards_scan_timestamp_unchanged(duo, rfid_tag, monkeypatch, mock_pub):
    from unittest.mock import MagicMock
    from modules.common.component_state import ChargepointState, CounterState
    from modules.common.store._chargepoint_internal import InternalChargepointValueStore
    from modules.internal_chargepoint_handler import chargepoint_module as internal_module

    monkeypatch.setattr(internal_module.time, "sleep", Mock())
    module = object.__new__(internal_module.ChargepointModule)
    module.store = Mock()
    module.store_internal = InternalChargepointValueStore(0)
    module.fault_state = Mock()
    module.old_chargepoint_state = ChargepointState(
        phases_in_use=3, imported=0, exported=0, power=0, currents=[0]*3,
        charge_state=False, plug_state=True)
    module.old_phases_in_use = 3
    module.client_error_context = MagicMock()
    module.client_error_context.error_counter_exceeded.return_value = False
    module._client = Mock()
    module._client.request_and_check_hardware.return_value = (
        SimpleNamespace(plug_state=True, charge_state=False, set_current=0, max_current=32), CounterState())
    module.version, module.current_branch, module.current_commit = "test", "test", "test"
    scanned_at = duo.clock.return_value - 1.125

    for _ in range(2):
        state = module.get_values(False, rfid_tag, scanned_at)
        assert state.rfid == rfid_tag
        assert state.rfid_timestamp == scanned_at
        mock_pub.pub.assert_any_call("openWB/set/internal_chargepoint/0/get/rfid_timestamp", scanned_at)

    # Nach der Quittierung darf kein alter Scanzeitstempel retained bleiben.
    module.get_values(False, None, None)
    mock_pub.pub.assert_any_call("openWB/set/internal_chargepoint/0/get/rfid_timestamp", None)


def test_processed_scan_remains_blocked_after_unplugging(duo, rfid_tag, monkeypatch):
    cp, partner = duo.chargepoints
    cp.data.get.plug_state = True
    cp.data.set.plug_time = duo.clock.return_value - 10
    scanned_at = duo.clock.return_value
    duo.reader.scan(rfid_tag, scanned_at)
    cp._validate_rfid()
    cp._link_rfid_to_cp()
    cp.data.set.plug_state_prev = True
    cp.data.get.plug_state = False
    monkeypatch.setattr(data.data.counter_all_data, "get_evu_counter", Mock(return_value=Mock()))
    monkeypatch.setattr(chargepoint_module, "Pub", Mock(return_value=duo.mqtt))
    monkeypatch.setattr(chargepoint_module.chargelog, "save_and_reset_data",
                        Mock(side_effect=lambda point, ev: point.reset_log_data()))

    cp._process_charge_stop()

    assert cp.data.set.rfid is None
    assert cp.data.set.rfid_timestamp == scanned_at
    duo.reader.scan(rfid_tag, scanned_at)
    for point in (cp, partner):
        point._validate_rfid()
        assert point.data.get.rfid is None
        assert point.data.set.rfid is None


@pytest.fixture()
def mock_data() -> None:
    data.data_init(Mock())
    data.data.cp_data["cp1"] = Chargepoint(1, None)
    data.data.cp_data["cp1"].template = CpTemplate()
    data.data.cp_data["cp1"].chargepoint_module = Mock()
    data.data.cp_data["cp1"].data.get.rfid = "1234"


@pytest.mark.parametrize(
    "partner_id, cp0_plug_state, cp1_plug_state, cp0_plug_time, cp1_plug_time, expected_set_rfid",
    [
        pytest.param(None, True, False, None, None, "1234", id="no duo"),
        pytest.param(1, True, False, None, None, "1234", id="second cp not plugged"),
        pytest.param(1, True, True, 1706868636, 1706868646, None, id="self first plugged"),
        pytest.param(1, True, True, 1706868636, 1706868626, "1234", id="second first plugged"),
        pytest.param(1, False, True, None, 1706868626, None,
                     id="second plugged, self not plugged yet, wait for plugging"),
    ])
def test_link_rfid_to_cp(partner_id: Optional[int],
                         cp0_plug_state: bool,
                         cp1_plug_state: bool,
                         cp0_plug_time: Optional[int],
                         cp1_plug_time: Optional[int],
                         expected_set_rfid: Optional[str],
                         mock_data,
                         monkeypatch):
    # setup
    cp = Chargepoint(0, None)
    cp.chargepoint_module = Mock()
    cp.data.get.rfid = "1234"
    cp.data.get.plug_state = cp0_plug_state
    cp.data.set.plug_time = cp0_plug_time
    data.data.cp_data["cp1"].data.get.plug_state = cp1_plug_state
    data.data.cp_data["cp1"].data.set.plug_time = cp1_plug_time
    data.data.cp_data["cp1"].data.config.ev = 1
    data.data.ev_data["ev1"] = Ev(1)

    mock_find_duo_partner = Mock(return_value=partner_id)
    monkeypatch.setattr(Chargepoint, "find_duo_partner", mock_find_duo_partner)

    # execution
    cp._link_rfid_to_cp()

    # evaluation
    assert cp.data.set.rfid == expected_set_rfid
    assert cp.data.get.rfid is None
    assert cp.data.get.rfid_timestamp is None
    # Die Auswahl darf auch am Partner erfolgen. Der gemeinsame Reader wird
    # unabhängig vom Ziel-LP nur einmal über den aufrufenden LP quittiert.
    cp.chargepoint_module.clear_rfid.assert_called_once_with()
    if partner_id is not None:
        partner = data.data.cp_data[f"cp{partner_id}"]
        assert partner.data.set.rfid == ("1234" if expected_set_rfid is None else None)
        assert partner.data.get.rfid is None
        assert partner.data.get.rfid_timestamp is None
        partner.chargepoint_module.clear_rfid.assert_not_called()


@pytest.fixture
def rfid_tag():
    """Ein an beiden Ladepunkten zugelassener Test-Tag."""
    return "04A1B2C3D4"


@pytest.fixture
def duo(monkeypatch, rfid_tag):
    """Zwei Ladepunkte mit gemeinsamer IP und gemeinsamem RFID-Leser."""
    # Die globale Testkonfiguration nach jedem Test wiederherstellen.
    monkeypatch.setattr(data, "data", None, raising=False)
    data.data_init(Mock())
    data.data.cp_data.clear()
    data.data.ev_data.clear()
    data.data.ev_data["ev0"] = Ev(0)
    data.data.optional_data.data.rfid.active = True

    mqtt = Mock(name="mqtt")
    monkeypatch.setattr(rfid, "Pub", Mock(return_value=mqtt))
    clock = Mock(name="clock", return_value=1_700_000_000)
    monkeypatch.setattr(rfid.timecheck, "create_timestamp", clock)

    chargepoints = []
    for number in (1, 2):
        cp = Chargepoint(number, None)
        cp.template = CpTemplate()
        cp.template.data.valid_tags = [rfid_tag, "ABC"]
        cp.template.data.disable_after_unplug = True
        cp.data.config.type = "external_openwb"
        cp.data.config.configuration = {"ip_address": "192.0.2.10"}
        cp.data.config.ev = 0
        cp.data.get.plug_state = False
        cp.data.get.charge_state = False
        cp.data.get.imported = 0
        cp.data.get.rfid = None
        cp.data.get.rfid_timestamp = None
        cp.data.set.rfid = None
        cp.data.set.manual_lock = True
        cp.data.set.log.imported_at_plugtime = 0
        cp.chargepoint_module = Mock(name=f"duo_hardware_cp{number}", spec=["clear_rfid"])
        data.data.cp_data[f"cp{number}"] = cp
        chargepoints.append(cp)

    def scan(tag, timestamp=None):
        # Der gemeinsame Leser meldet denselben Scan an beide Duo-Ladepunkte.
        for cp in chargepoints:
            cp.data.get.rfid = tag
            if timestamp is not None:
                cp.data.get.rfid_timestamp = timestamp

    reader = Mock(name="rfid_reader", spec=["scan"])
    reader.scan.side_effect = scan
    return SimpleNamespace(chargepoints=chargepoints, reader=reader, mqtt=mqtt, clock=clock)


@pytest.fixture
def duo_control_cycle(duo, rfid_tag, monkeypatch, caplog):
    """Echte Prepare-Schleife und echte Chargepoints; keine reale Ladung."""
    default_ev = data.data.ev_data["ev0"]
    default_ev.data.name = "Standardfahrzeug"
    tagged_ev = Ev(1)
    tagged_ev.data.name = "RFID-Testfahrzeug"
    tagged_ev.data.tag_id = [rfid_tag]
    data.data.ev_data["ev1"] = tagged_ev
    monkeypatch.setattr(chargepoint_module, "Pub", Mock(return_value=duo.mqtt))

    # Reale Konfiguration statt Mock von is_charging_possible(): Eine aktive
    # Netzschutzsperre verhindert nur das Laden, nicht die RFID-Zuordnung.
    general = data.data.general_data.data
    general.grid_protection_configured = True
    general.grid_protection_active = True
    general.grid_protection_timestamp = None

    # Nur nicht beteiligte PV-/Speicher-/Zähler-/IO-Subsysteme ersetzen.
    for name in ("io_actions", "pv_all_data", "bat_all_data", "consumer_all_data", "counter_all_data"):
        monkeypatch.setattr(data.data, name, Mock(name=name))
    data.data.counter_all_data.get_list_of_elements_per_level.return_value = []
    data.data.consumer_data.clear()
    monkeypatch.setattr(data.data, "print_all", Mock())
    production_prepare = prepare.Prepare()

    def run_cycle():
        production_prepare.setup_algorithm()
        # update()/Prepare fangen Fehler intern ab: Nicht stillschweigend
        # weiterprüfen, falls ein unvollständiger Aufbau einen Fehler auslöst.
        errors = [record.getMessage() for record in caplog.records if record.levelno >= 40]
        assert not errors, f"Interner Fehler im Produktions-Regelzyklus: {errors}"

    return SimpleNamespace(run=run_cycle, default_ev=default_ev, tagged_ev=tagged_ev)


@pytest.mark.parametrize("module_type", ["external_openwb", "internal_openwb"])
def test_duo_partner_is_detected(duo, module_type):
    for cp in duo.chargepoints:
        cp.data.config.type = module_type
    cp1, cp2 = duo.chargepoints
    assert cp1.find_duo_partner() == cp2.num
    assert cp2.find_duo_partner() == cp1.num


@pytest.mark.parametrize("plugged_index", [0, 1], ids=["Ladepunkt-1", "Ladepunkt-2"])
@pytest.mark.parametrize("reverse_order", [False, True], ids=["Reihenfolge-1-2", "Reihenfolge-2-1"])
def test_scan_is_assigned_only_to_plugged_chargepoint(
        duo, rfid_tag, plugged_index, reverse_order):
    plugged = duo.chargepoints[plugged_index]
    other = duo.chargepoints[1 - plugged_index]
    plugged.data.get.plug_state = True
    plugged.data.set.plug_time = duo.clock.return_value - 10

    duo.reader.scan(rfid_tag)
    order = list(reversed(duo.chargepoints)) if reverse_order else duo.chargepoints
    # RFID-relevanter Ausschnitt eines Regelzyklus, ohne Laderegelung zu starten.
    for cp in order:
        cp._validate_rfid()
        if cp.data.get.rfid is not None and cp.data.get.plug_state:
            cp._link_rfid_to_cp()

    duo.reader.scan.assert_called_once_with(rfid_tag)
    assert plugged.data.set.rfid == rfid_tag
    assert other.data.set.rfid is None
    assert other.data.set.manual_lock is True
    for cp in duo.chargepoints:
        assert cp.data.get.rfid is None
        assert cp.data.get.rfid_timestamp is None
    plugged.chargepoint_module.clear_rfid.assert_called_once_with()
    other.chargepoint_module.clear_rfid.assert_not_called()
    duo.mqtt.pub.assert_any_call(f"openWB/set/chargepoint/{other.num}/get/rfid", None)


@pytest.mark.parametrize("elapsed", [300, 301], ids=["bei-300s-gueltig", "nach-301s-verworfen"])
def test_scan_timeout_without_vehicle(duo, duo_control_cycle, rfid_tag, elapsed):
    default_ev = duo_control_cycle.default_ev
    duo.reader.scan(rfid_tag)
    duo_control_cycle.run()
    assert all(cp.data.get.connected_vehicle.info.id == duo_control_cycle.tagged_ev.num
               for cp in duo.chargepoints)
    duo.clock.return_value += elapsed
    duo_control_cycle.run()

    for cp in duo.chargepoints:
        assert cp.data.set.rfid is None
        assert cp.data.get.plug_state is False
        assert cp.data.set.manual_lock is True
        if elapsed == 300:
            assert cp.data.get.rfid == rfid_tag
            assert cp.data.get.rfid_timestamp == duo.clock.return_value - elapsed
            assert cp.data.get.connected_vehicle.info.id == duo_control_cycle.tagged_ev.num
            cp.chargepoint_module.clear_rfid.assert_not_called()
        else:
            assert cp.data.get.rfid is None
            assert cp.data.get.rfid_timestamp is None
            assert cp.data.get.connected_vehicle.info.id == default_ev.num
            duo.mqtt.pub.assert_any_call(f"openWB/set/chargepoint/{cp.num}/get/rfid", None)
    if elapsed == 301:
        # Ein gemeinsamer Scan wird genau einmal am gemeinsamen Leser quittiert.
        assert sum(cp.chargepoint_module.clear_rfid.call_count for cp in duo.chargepoints) == 1
        assert any("verworfen" in (cp.data.get.state_str or "") for cp in duo.chargepoints)


@pytest.mark.parametrize("plugged_index", [0, 1], ids=["Anstecken-LP1", "Anstecken-LP2"])
@pytest.mark.parametrize("reverse_order", [False, True], ids=["Zyklus-LP1-LP2", "Zyklus-LP2-LP1"])
def test_production_loop_resets_vehicle_by_next_cycle(
        duo, duo_control_cycle, rfid_tag, plugged_index, reverse_order):
    """Eine vorläufige Anzeige darf höchstens bis zum Folgezyklus bestehen."""
    order = list(reversed(duo.chargepoints)) if reverse_order else duo.chargepoints
    data.data.cp_data = {f"cp{cp.num}": cp for cp in order}
    plugged = duo.chargepoints[plugged_index]
    other = duo.chargepoints[1 - plugged_index]
    duo.reader.scan(rfid_tag)
    duo_control_cycle.run()
    assert all(cp.data.get.connected_vehicle.info.id == 1 for cp in duo.chargepoints)

    duo.clock.return_value += 60
    plugged.data.get.plug_state = True
    duo_control_cycle.run()
    first_cycle_id = other.data.get.connected_vehicle.info.id
    assert other.data.get.rfid is None
    assert other.data.config.ev == 0
    # Ein unmittelbarer Reset ist ebenfalls zulässig. Entscheidend ist der
    # garantierte Reset im Folgezyklus, nicht eine bestimmte alte Verzögerung.
    assert first_cycle_id in (duo_control_cycle.default_ev.num, duo_control_cycle.tagged_ev.num)

    duo_control_cycle.run()
    next_cycle_id = other.data.get.connected_vehicle.info.id
    assert next_cycle_id == 0, "Fahrzeug bleibt auch im Folgezyklus am freien LP zugeordnet."
    assert plugged.data.get.connected_vehicle.info.id == 1


@pytest.mark.parametrize("duo_mode, reverse_order", [(False, False), (True, False), (True, True)],
                         ids=["Einzel-LP", "Duo-LP1-LP2", "Duo-LP2-LP1"])
@pytest.mark.parametrize("assigned", [False, True], ids=["Ohne-RFID-Zuordnung", "Mit-RFID-Zuordnung"])
def test_new_scan_after_charging_starts_preserves_existing_assignment(
        duo, rfid_tag, duo_mode, reverse_order, assigned):
    """Nach Energiebezug darf ein neuer Scan laufende Zuordnungen nicht ersetzen."""
    chargepoints = duo.chargepoints if duo_mode else duo.chargepoints[:1]
    if not duo_mode:
        data.data.cp_data.pop(f"cp{duo.chargepoints[1].num}")
    for index, cp in enumerate(chargepoints):
        tag = (rfid_tag, "ABC")[index]
        ev = Ev(index + 1)
        ev.data.tag_id = [tag]
        data.data.ev_data[f"ev{ev.num}"] = ev
        cp.data.config.ev = ev.num
        cp.data.set.rfid = tag if assigned else None
        cp.data.set.manual_lock = False
        cp.data.get.plug_state = True
        cp.data.get.charge_state = True
        cp.data.set.plug_time = duo.clock.return_value - 60 - index
        cp.data.set.log.imported_at_plugtime = 1000
        cp.data.get.imported = 1100
        cp.template.data.valid_tags.append("NEUER-TAG")

    duo.reader.scan("NEUER-TAG")
    order = list(reversed(chargepoints)) if reverse_order else chargepoints
    for cp in order:
        cp._validate_rfid()
        if cp.data.get.rfid is not None:
            cp._link_rfid_to_cp()
    for index, cp in enumerate(chargepoints):
        assert cp.data.set.rfid == ((rfid_tag, "ABC")[index] if assigned else None)
        assert cp.data.config.ev == index + 1
        assert cp.data.set.manual_lock is False
        assert cp.data.get.charge_state is True
        assert cp.data.get.rfid is None
        assert cp.data.get.rfid_timestamp is None
    assert sum(cp.chargepoint_module.clear_rfid.call_count for cp in chargepoints) == 1
    expected_message = ("Beide Ladepunkte sind bereits zugeordnet oder laden."
                        " Es wird kein weiterer ID-Tag akzeptiert." if duo_mode else
                        "Nach Ladestart wird kein anderer ID-Tag akzeptiert.")
    assert all(expected_message in (cp.data.get.state_str or "") for cp in chargepoints)


@pytest.mark.parametrize("selected_index", [0, 1], ids=["Ziel-LP1", "Ziel-LP2"])
@pytest.mark.parametrize("reverse_order", [False, True], ids=["LP1-LP2", "LP2-LP1"])
def test_duo_rfid_authorizes_only_assigned_chargepoint(
        duo, rfid_tag, monkeypatch, caplog, selected_index, reverse_order):
    """Echte update()- und Freigabelogik, ohne Netzschutz als Abkürzung."""
    data.data.general_data.data.grid_protection_configured = False
    data.data.ev_data["ev1"] = Ev(1)
    data.data.ev_data["ev1"].data.tag_id = [rfid_tag]
    monkeypatch.setattr(chargepoint_module, "Pub", Mock(return_value=duo.mqtt))
    order = list(reversed(duo.chargepoints)) if reverse_order else duo.chargepoints
    selected = duo.chargepoints[selected_index]
    other = duo.chargepoints[1 - selected_index]
    permissions = {cp.num: [] for cp in duo.chargepoints}

    for cp in duo.chargepoints:
        original = cp.is_charging_possible

        def record_permission(cp=cp, original=original):
            result = original()
            permissions[cp.num].append(result[0])
            # Erst die echte Freigabe inklusive ihrer Zustandsänderungen prüfen,
            # danach nur die nachgelagerte Stromberechnung ausblenden.
            return False, result[1] or "Test: Stromberechnung ausgeblendet"

        monkeypatch.setattr(cp, "is_charging_possible", record_permission)
        monkeypatch.setattr(cp, "_process_charge_stop", Mock())

    for cp in duo.chargepoints:
        cp.data.get.plug_state = True
        cp.data.set.plug_time = duo.clock.return_value - (10 if cp is selected else 20)
    duo.reader.scan(rfid_tag)

    for cp in order:
        cp.update(data.data.ev_data)
    assert selected.data.set.rfid == rfid_tag
    assert selected.data.set.manual_lock is False
    assert other.data.set.rfid is None
    assert other.data.set.manual_lock is True

    for cp in order:
        cp.update(data.data.ev_data)
    assert permissions[selected.num] == [False, True]
    assert permissions[other.num] == [False, False]
    assert other.data.set.manual_lock is True
    assert not [record for record in caplog.records if record.levelno >= 40]


@pytest.mark.parametrize("duo_mode, source", [
    (False, "get.rfid"), (False, "set.rfid"), (False, "vehicle_id"), (True, "vehicle_id")])
def test_rfid_authorization_is_preserved(duo, rfid_tag, duo_mode, source):
    data.data.general_data.data.grid_protection_configured = False
    cp = duo.chargepoints[0]
    if not duo_mode:
        data.data.cp_data.pop(f"cp{duo.chargepoints[1].num}")
    cp.data.get.plug_state = True
    if source == "get.rfid":
        cp.data.get.rfid = rfid_tag
    elif source == "set.rfid":
        cp.data.set.rfid = rfid_tag
    else:
        cp.data.get.vehicle_id = rfid_tag
    cp._is_manual_lock_inactive()
    assert cp.data.set.manual_lock is False
    assert cp.is_charging_possible()[0] is True


@pytest.mark.parametrize("plug_times", [(0, 0), (1000, 1000), (None, None), (None, 1000), (1000, None)])
@pytest.mark.parametrize("reverse_order", [False, True], ids=["LP1-LP2", "LP2-LP1"])
def test_duo_rfid_waits_when_plug_times_are_equal_or_missing(duo, rfid_tag, plug_times, reverse_order):
    """Gleiche oder fehlende Zeiten: Auch ein weiterer Scan darf keinen LP freigeben."""
    data.data.general_data.data.grid_protection_configured = False
    order = list(reversed(duo.chargepoints)) if reverse_order else duo.chargepoints
    for cp, plug_time in zip(duo.chargepoints, plug_times):
        cp.data.get.plug_state = True
        cp.data.set.plug_time = plug_time
    for tag in (rfid_tag, "ABC"):
        duo.reader.scan(tag)
        for cp in order:
            cp._validate_rfid()
            cp._link_rfid_to_cp()
            assert cp.is_charging_possible()[0] is False
        for cp in duo.chargepoints:
            assert cp.data.set.rfid is None
            assert cp.data.get.rfid == tag
            assert cp.data.set.manual_lock is True
            cp.chargepoint_module.clear_rfid.assert_not_called()


@pytest.mark.parametrize("source_index", [0, 1], ids=["Quittierung-LP1", "Quittierung-LP2"])
def test_duo_rfid_acknowledges_shared_reader(duo, rfid_tag, source_index):
    for cp in duo.chargepoints:
        cp.data.get.rfid = rfid_tag
        cp.data.get.rfid_timestamp = 1000
        cp.data.set.rfid = rfid_tag
    cp = duo.chargepoints[source_index]
    partner = duo.chargepoints[1 - source_index]

    cp._clear_pending_rfid(rfid_tag, partner)

    cp.chargepoint_module.clear_rfid.assert_called_once_with()
    partner.chargepoint_module.clear_rfid.assert_not_called()
    for point in duo.chargepoints:
        assert point.data.get.rfid is None
        assert point.data.get.rfid_timestamp is None
        assert point.data.set.rfid == rfid_tag


@pytest.mark.parametrize("load_defaults", [(False, False), (True, True), (True, False), (False, True)])
@pytest.mark.parametrize("source_index", [0, 1], ids=["Timeout-LP1", "Timeout-LP2"])
@pytest.mark.parametrize("elapsed", [300, 301], ids=["Noch-gueltig", "Abgelaufen"])
def test_duo_timeout_reset_respects_both_vehicle_profiles(
        duo, rfid_tag, load_defaults, source_index, elapsed):
    """Beim gemeinsamen Timeout jedes Profil vor dem Löschen der Tags auswerten."""
    for index, cp in enumerate(duo.chargepoints):
        ev = Ev(index + 1)
        ev.charge_template.data.load_default = load_defaults[index]
        data.data.ev_data[f"ev{ev.num}"] = ev
        cp.data.config.ev = ev.num
        cp.data.set.charging_ev_data = ev
        cp.data.set.manual_lock = False
        cp.template.data.disable_after_unplug = index == 0
    duo.reader.scan(rfid_tag)
    for cp in duo.chargepoints:
        cp._validate_rfid()
    duo.clock.return_value += elapsed

    duo.chargepoints[source_index]._validate_rfid()

    for index, cp in enumerate(duo.chargepoints):
        if elapsed == 300:
            assert cp.data.config.ev == index + 1
            assert cp.data.set.manual_lock is False
            assert cp.data.get.rfid == rfid_tag
            assert cp.data.get.rfid_timestamp == duo.clock.return_value - elapsed
        else:
            assert cp.data.config.ev == (0 if load_defaults[index] else index + 1)
            assert cp.data.set.manual_lock is (index == 0)
            assert cp.data.get.rfid is None
            assert cp.data.get.rfid_timestamp is None
        assert cp.data.set.rfid is None
    assert sum(cp.chargepoint_module.clear_rfid.call_count for cp in duo.chargepoints) == (elapsed == 301)


@pytest.mark.parametrize("source_index", [0, 1], ids=["Scan-LP1", "Scan-LP2"])
@pytest.mark.parametrize("source_plugged", [False, True], ids=["Quelle-leer", "Quelle-eingesteckt"])
def test_duo_energy_check_uses_target_instead_of_calling_chargepoint(
        duo, rfid_tag, source_index, source_plugged):
    """Energiebezug am aufrufenden LP darf den Tag für den anderen nicht verwerfen."""
    cp = duo.chargepoints[source_index]
    target = duo.chargepoints[1 - source_index]
    cp.data.get.plug_state = source_plugged
    cp.data.set.log.imported_at_plugtime = 1000
    cp.data.get.imported = 1100
    cp.data.set.rfid = "ABC" if source_plugged else None
    target.data.get.plug_state = True
    cp.data.set.plug_time = duo.clock.return_value - 20
    target.data.set.plug_time = duo.clock.return_value - 10
    target.data.set.log.imported_at_plugtime = 1000
    target.data.get.imported = 1000
    duo.reader.scan(rfid_tag)

    cp._validate_rfid()

    assert cp.data.get.rfid is None
    assert cp.data.get.rfid_timestamp is None
    assert target.data.get.rfid == rfid_tag
    assert all(point.chargepoint_module.clear_rfid.call_count == 0 for point in duo.chargepoints)
    target._validate_rfid()
    target._link_rfid_to_cp()
    assert target.data.set.rfid == rfid_tag
    assert cp.data.set.rfid == ("ABC" if source_plugged else None)
    assert all(point.data.get.rfid is None for point in duo.chargepoints)


@pytest.mark.parametrize("running_index", [0, 1])
@pytest.mark.parametrize("reverse_order", [False, True])
@pytest.mark.parametrize("meter", [0, 1000], ids=["Zaehler-null", "Zaehler-unveraendert"])
def test_duo_scan_waits_at_free_partner_when_other_charges_without_meter_progress(
        duo, rfid_tag, running_index, reverse_order, meter):
    running = duo.chargepoints[running_index]
    free = duo.chargepoints[1 - running_index]
    running.data.get.plug_state = True
    running.data.get.charge_state = True
    running.data.set.plug_time = duo.clock.return_value - 60
    running.data.set.log.imported_at_plugtime = meter
    running.data.get.imported = meter
    running.data.set.manual_lock = False
    running.data.get.state_str = "Lädt bereits"
    order = list(reversed(duo.chargepoints)) if reverse_order else duo.chargepoints
    duo.reader.scan(rfid_tag)

    for cp in order:
        cp._validate_rfid()
        if cp.data.get.rfid is not None and cp.data.get.plug_state:
            cp._link_rfid_to_cp()

    assert running.data.set.rfid is None
    assert running.data.get.rfid is None
    assert running.data.get.rfid_timestamp is None
    assert running.data.get.state_str == "Lädt bereits"
    assert running.data.set.manual_lock is False
    assert free.data.set.rfid is None
    assert free.data.get.rfid == rfid_tag
    assert free.data.get.rfid_timestamp == duo.clock.return_value
    assert "5 Minuten" in free.data.get.state_str
    assert all(cp.chargepoint_module.clear_rfid.call_count == 0 for cp in duo.chargepoints)

    duo.clock.return_value += 60
    free.data.get.plug_state = True
    free.data.set.plug_time = duo.clock.return_value
    for cp in order:
        cp._validate_rfid()
        if cp.data.get.rfid is not None and cp.data.get.plug_state:
            cp._link_rfid_to_cp()

    assert free.data.set.rfid == rfid_tag
    assert running.data.set.rfid is None
    assert running.data.get.state_str == "Lädt bereits"
    assert running.data.get.charge_state is True
    assert all(cp.data.get.rfid is None for cp in duo.chargepoints)
    assert sum(cp.chargepoint_module.clear_rfid.call_count for cp in duo.chargepoints) == 1


@pytest.mark.parametrize("duo_mode", [False, True], ids=["Einzel-LP", "Duo"])
@pytest.mark.parametrize("charge_state", [False, True], ids=["Laedt-nicht", "Ladesignal-aktiv"])
@pytest.mark.parametrize("energy_delivered", [False, True], ids=["Vor-Energiebezug", "Nach-Energiebezug"])
def test_only_single_chargepoint_allows_reselection_while_duo_preserves_assignment(
        duo, rfid_tag, monkeypatch, caplog, duo_mode, charge_state, energy_delivered):
    """Nur Einzel-LP dürfen A vor Energiebezug ersetzen; Duo hält A bis zum Abstecken."""
    data.data.general_data.data.grid_protection_configured = False
    monkeypatch.setattr(chargepoint_module, "Pub", Mock(return_value=duo.mqtt))
    for number, tag in ((1, rfid_tag), (2, "ABC")):
        ev = Ev(number)
        ev.data.tag_id = [tag]
        data.data.ev_data[f"ev{number}"] = ev
    cp, partner = duo.chargepoints
    chargepoints = duo.chargepoints if duo_mode else [cp]
    if not duo_mode:
        data.data.cp_data.pop(f"cp{partner.num}")
    cp.data.get.plug_state = True
    cp.data.set.plug_time = duo.clock.return_value - 60
    cp.data.get.charge_state = charge_state
    cp.data.set.log.imported_at_plugtime = 1000
    cp.data.get.imported = 1100 if energy_delivered else 1000
    cp.data.set.rfid = rfid_tag
    cp.data.set.manual_lock = False
    cp.data.config.ev = 1
    cp.data.set.charging_ev_data = data.data.ev_data["ev1"]
    duo.reader.scan("ABC")

    # update() inklusive echter RFID- und Freigabeprüfung ausführen; nur
    # die anschließende Stromberechnung/Zählerbehandlung ausblenden.
    with monkeypatch.context() as patcher:
        for point in chargepoints:
            original = point.is_charging_possible

            def suppress_current(original=original):
                result = original()
                return False, result[1] or "Test: Stromberechnung ausgeblendet"

            patcher.setattr(point, "is_charging_possible", suppress_current)
            patcher.setattr(point, "_process_charge_stop", Mock())
        for point in chargepoints:
            point.update(data.data.ev_data)
    cp.update_ev(data.data.ev_data)

    expected_tag = rfid_tag if duo_mode or energy_delivered else "ABC"
    expected_ev = 1 if duo_mode or energy_delivered else 2
    assert cp.data.set.rfid == expected_tag
    assert cp.data.config.ev == expected_ev
    assert cp.data.set.charging_ev_data.num == expected_ev
    assert cp.data.get.connected_vehicle.info.id == expected_ev
    assert cp.data.set.manual_lock is False
    # Bei einer Duo wartet B am leeren Partner, auch vor Energiebezug.
    assert cp.data.get.rfid is None
    if duo_mode:
        assert partner.data.set.rfid is None
        assert partner.data.set.manual_lock is True
        assert partner.data.get.rfid == "ABC"
    assert not [record for record in caplog.records if record.levelno >= 40]


@pytest.mark.parametrize("plug_times, running_index", [
    ((10, 20), None), ((20, 10), None), ((10, 10), None), ((None, 10), None),
    ((10, 20), 0), ((10, 20), 1),
])
@pytest.mark.parametrize("reverse_order", [False, True], ids=["LP1-LP2", "LP2-LP1"])
def test_duo_new_scan_does_not_change_existing_assignments(
        duo, rfid_tag, plug_times, running_index, reverse_order):
    """Beide zugeordnet oder ein LP lädt: Scan quittieren und beide informieren."""
    for index, cp in enumerate(duo.chargepoints):
        cp.data.get.plug_state = True
        cp.data.set.rfid = None if index == running_index else (rfid_tag, "ABC")[index]
        cp.data.get.charge_state = index == running_index
        age = plug_times[index]
        cp.data.set.plug_time = duo.clock.return_value - age if age is not None else None
        cp.data.set.log.imported_at_plugtime = 1000
        cp.data.get.imported = 1000
        cp.template.data.valid_tags.append("NEUER-TAG")
    duo.reader.scan("NEUER-TAG")
    order = list(reversed(duo.chargepoints)) if reverse_order else duo.chargepoints

    for cp in order:
        cp._validate_rfid()
        if cp.data.get.rfid is not None:
            cp._link_rfid_to_cp()

    for index, cp in enumerate(duo.chargepoints):
        expected = None if index == running_index else (rfid_tag, "ABC")[index]
        assert cp.data.set.rfid == expected
        assert cp.data.get.rfid is None
        assert cp.data.get.rfid_timestamp is None
        assert cp.data.get.state_str == ("Beide Ladepunkte sind bereits zugeordnet oder laden."
                                         " Es wird kein weiterer ID-Tag akzeptiert.")
    assert sum(cp.chargepoint_module.clear_rfid.call_count for cp in duo.chargepoints) == 1


@pytest.mark.parametrize("running_index", [None, 0, 1], ids=["Beide-leer", "Belegt-LP1", "Belegt-LP2"])
@pytest.mark.parametrize("reverse_order", [False, True], ids=["LP1-LP2", "LP2-LP1"])
@pytest.mark.parametrize("event", ["timeout", "invalid-tag", "rfid-disabled"])
def test_scan_rejection_and_messages_affect_only_available_chargepoints(
        duo, running_index, reverse_order, event):
    running = duo.chargepoints[running_index] if running_index is not None else None
    available = [cp for cp in duo.chargepoints if cp is not running]
    if running is not None:
        running.data.get.plug_state = True
        running.data.get.charge_state = True
        running.data.set.log.imported_at_plugtime = 1000
        running.data.get.imported = 1100
        running.data.set.manual_lock = False
        running.data.get.state_str = "Lädt bereits"
    duo.reader.scan("UNBEKANNT" if event == "invalid-tag" else "ABC")
    order = list(reversed(duo.chargepoints)) if reverse_order else duo.chargepoints
    if event == "timeout":
        for cp in order:
            cp._validate_rfid()
            if cp.data.get.rfid is not None:
                cp._link_rfid_to_cp()
        # Zweite Prüfung setzt den Wartehinweis, aber nur am leeren LP.
        for cp in order:
            cp._validate_rfid()
        assert all("5 Minuten" in cp.data.get.state_str for cp in available)
        if running is not None:
            assert running.data.get.state_str == "Lädt bereits"
        duo.clock.return_value += 301
    elif event == "rfid-disabled":
        data.data.optional_data.data.rfid.active = False

    for cp in order:
        cp._validate_rfid()
        if cp.data.get.rfid is not None:
            cp._link_rfid_to_cp()

    if running is not None:
        assert running.data.get.state_str == "Lädt bereits"
        assert running.data.set.manual_lock is False
        assert running.data.get.charge_state is True
        assert running.data.get.imported == 1100
    expected = {"timeout": "Daher wird dieser verworfen", "invalid-tag": "nicht gültig",
                "rfid-disabled": "nicht aktiviert"}[event]
    for cp in available:
        assert expected in cp.data.get.state_str
        assert cp.data.set.manual_lock is True
    assert all(cp.data.set.rfid is None for cp in duo.chargepoints)
    assert all(cp.data.get.rfid is None for cp in duo.chargepoints)
    assert all(cp.data.get.rfid_timestamp is None for cp in duo.chargepoints)
    assert sum(cp.chargepoint_module.clear_rfid.call_count for cp in duo.chargepoints) == 1


@pytest.mark.parametrize("reverse_order", [False, True])
@pytest.mark.parametrize("same_card", [False, True], ids=["Andere-Karte", "Gleiche-Freigabekarte"])
def test_duo_authorizes_two_waiting_vehicles_sequentially_without_energy_consumption(
        duo, rfid_tag, reverse_order, same_card):
    """Erster Scan: letzter Stecker. Zweiter Scan: übriger LP, ohne vorherigen Ladestart."""
    older, latest = duo.chargepoints
    for cp, age in ((older, 20), (latest, 10)):
        cp.data.get.plug_state = True
        cp.data.set.plug_time = duo.clock.return_value - age
    order = list(reversed(duo.chargepoints)) if reverse_order else duo.chargepoints
    duo.reader.scan(rfid_tag)
    for _ in range(2):
        for cp in order:
            cp._validate_rfid()
            if cp.data.get.rfid is not None and cp.data.get.plug_state:
                cp._link_rfid_to_cp()
            cp.is_charging_possible()
    assert latest.data.set.rfid == rfid_tag
    assert latest.data.set.manual_lock is False
    assert older.data.set.rfid is None
    assert older.data.set.manual_lock is True
    assert all(cp.data.get.rfid is None for cp in duo.chargepoints)
    assert sum(cp.chargepoint_module.clear_rfid.call_count for cp in duo.chargepoints) == 1

    # Nach gemeinsamer Quittierung ist die nächste Meldung ein neuer Scan,
    # auch wenn dieselbe profilbezogene Freigabekarte erneut verwendet wird.
    duo.clock.return_value += 10
    tag = rfid_tag if same_card else "ABC"
    duo.reader.scan(tag)
    for _ in range(2):
        for cp in order:
            cp._validate_rfid()
            if cp.data.get.rfid is not None and cp.data.get.plug_state:
                cp._link_rfid_to_cp()
            cp.is_charging_possible()
    assert latest.data.set.rfid == rfid_tag
    assert older.data.set.rfid == tag
    assert all(cp.data.set.manual_lock is False for cp in duo.chargepoints)
    assert all(cp.data.get.charge_state is False for cp in duo.chargepoints)
    assert sum(cp.chargepoint_module.clear_rfid.call_count for cp in duo.chargepoints) == 2


@pytest.mark.parametrize("first_index", [0, 1])
@pytest.mark.parametrize("reverse_order", [False, True])
@pytest.mark.parametrize("first_plug_offset", [-10, 10], ids=["Ein-Auto-wartet", "Beide-spaeter-erkannt"])
def test_duo_ambiguous_plug_order_waits_for_new_scan(
        duo, rfid_tag, first_index, reverse_order, first_plug_offset):
    duo.reader.scan(rfid_tag)
    for cp in duo.chargepoints:
        cp._validate_rfid()
    scanned_at = duo.clock.return_value
    for index, cp in enumerate(duo.chargepoints):
        cp.data.get.plug_state = True
        cp.data.set.plug_time = scanned_at + (first_plug_offset if index == first_index else 20)
    duo.clock.return_value += 30
    order = list(reversed(duo.chargepoints)) if reverse_order else duo.chargepoints
    for _ in range(2):
        for cp in order:
            cp._validate_rfid()
            if cp.data.get.rfid is not None:
                cp._link_rfid_to_cp()
    assert all(cp.data.set.rfid is None for cp in duo.chargepoints)
    assert all(cp.data.set.rfid_timestamp is None for cp in duo.chargepoints)
    assert all(cp.data.get.rfid == rfid_tag for cp in duo.chargepoints)
    assert sum(cp.chargepoint_module.clear_rfid.call_count for cp in duo.chargepoints) == 0

    duo.reader.scan(rfid_tag, duo.clock.return_value)
    for cp in order:
        cp._validate_rfid()
        if cp.data.get.rfid is not None:
            cp._link_rfid_to_cp()
    assert duo.chargepoints[1 - first_index].data.set.rfid == rfid_tag
    assert duo.chargepoints[first_index].data.set.rfid is None
    assert sum(cp.chargepoint_module.clear_rfid.call_count for cp in duo.chargepoints) == 1


@pytest.mark.parametrize(
    "plug_after", [299, 301, None], ids=["Vor-Frist", "Nach-Frist", "Zeit-fehlt"])
@pytest.mark.parametrize("plugged_index", [0, 1])
def test_duo_timeout_with_plugged_target(
        duo, rfid_tag, plug_after, plugged_index):
    duo.reader.scan(rfid_tag)
    for cp in duo.chargepoints:
        cp._validate_rfid()
    cp = duo.chargepoints[plugged_index]
    cp.data.get.plug_state = True
    cp.data.set.plug_time = duo.clock.return_value + plug_after if plug_after is not None else None
    duo.clock.return_value += 360
    for _ in range(2):
        for point in duo.chargepoints:
            point._validate_rfid()
            if point.data.get.rfid is not None and point.data.get.plug_state:
                point._link_rfid_to_cp()
    assert cp.data.set.rfid == rfid_tag
    assert duo.chargepoints[1 - plugged_index].data.set.rfid is None
    assert all(point.data.get.rfid is None for point in duo.chargepoints)


def test_duo_new_tag_at_real_input_preserves_running_timeout(duo, rfid_tag):
    from helpermodules.subdata import SubData

    duo.reader.scan(rfid_tag)
    for cp in duo.chargepoints:
        cp._validate_rfid()
    scanned_at = duo.clock.return_value
    duo.clock.return_value += 299
    # Wie in Data.__copy_cp_data() werden neue CP-Objekte für den Regelzyklus
    # angelegt. Die vorhandene Frist bleibt beim Wechsel von A auf B bestehen.
    cps = [copy.deepcopy(cp) for cp in duo.chargepoints]
    data.data.cp_data = {f"cp{cp.num}": cp for cp in cps}
    handler = object.__new__(SubData)
    for cp in cps:
        handler.set_json_payload_class(cp.data.get, SimpleNamespace(
            topic=f"openWB/chargepoint/{cp.num}/get/rfid", payload=b'"ABC"'))
        assert cp.data.get.rfid_timestamp == scanned_at
    for cp in cps:
        cp._validate_rfid()
    assert all(cp.data.get.rfid_timestamp == scanned_at for cp in cps)
    assert all(cp.data.get.rfid == "ABC" for cp in cps)
    duo.clock.return_value += 1
    for cp in cps:
        # Wiederholte Meldungen verlängern den Timer nicht.
        handler.set_json_payload_class(cp.data.get, SimpleNamespace(
            topic=f"openWB/chargepoint/{cp.num}/get/rfid", payload=b'"ABC"'))
        cp._validate_rfid()
        assert cp.data.get.rfid == "ABC"
        assert cp.data.get.rfid_timestamp == scanned_at
    duo.clock.return_value += 1
    cps[0]._validate_rfid()
    assert all(cp.data.get.rfid is None for cp in cps)


@pytest.mark.parametrize("source_index", [0, 1])
@pytest.mark.parametrize("event", ["invalid", "timeout", "pending"])
def test_duo_background_copy_does_not_modify_global_scan(duo, rfid_tag, source_index, event):
    duo.reader.scan("UNBEKANNT" if event == "invalid" else rfid_tag)
    if event == "timeout":
        for cp in duo.chargepoints:
            cp.data.get.rfid_timestamp = duo.clock.return_value - 301
    before = [(cp.data.get.rfid, cp.data.get.rfid_timestamp, cp.data.get.state_str,
               cp.data.config.ev, cp.data.set.rfid, cp.data.set.manual_lock) for cp in duo.chargepoints]
    background_cp = copy.deepcopy(duo.chargepoints[source_index])
    background_cp.update_ev(data.data.ev_data)
    after = [(cp.data.get.rfid, cp.data.get.rfid_timestamp, cp.data.get.state_str,
              cp.data.config.ev, cp.data.set.rfid, cp.data.set.manual_lock) for cp in duo.chargepoints]
    assert after == before
    background_cp.chargepoint_module.clear_rfid.assert_not_called()
    assert all(cp.chargepoint_module.clear_rfid.call_count == 0 for cp in duo.chargepoints)
    assert not [call for call in duo.mqtt.pub.call_args_list if
                call.args[0].endswith(("/get/rfid", "/get/rfid_timestamp"))]


@pytest.mark.parametrize("duo_mode", [False, True], ids=["Einzel-LP", "Duo"])
@pytest.mark.parametrize("committed", [False, True], ids=["Vorlaeufig", "Zugeordnet"])
def test_duo_autolock_uses_only_assigned_tag(duo, rfid_tag, duo_mode, committed):
    cp, partner = duo.chargepoints
    if not duo_mode:
        data.data.cp_data.pop(f"cp{partner.num}")
    cp.data.get.plug_state = True
    cp.data.set.manual_lock = False
    cp.template.is_locked_by_autolock = Mock(return_value=True)
    if committed:
        cp.data.set.rfid = rfid_tag
    else:
        cp.data.get.rfid = rfid_tag
    possible, message = cp.is_charging_possible()
    assert possible is (committed or not duo_mode)
    if duo_mode and not committed:
        assert "Sperren nach Uhrzeit" in message


@pytest.mark.parametrize("unplugged_index", [0, 1])
@pytest.mark.parametrize("reverse_order", [False, True])
@pytest.mark.parametrize("stale_charge_state", [False, True])
def test_duo_scan_during_unplug_cycle_is_preserved_and_ocpp_keeps_old_tag(
        duo, rfid_tag, unplugged_index, reverse_order, stale_charge_state, monkeypatch, caplog):
    unplugged = duo.chargepoints[unplugged_index]
    partner = duo.chargepoints[1 - unplugged_index]
    general = data.data.general_data.data
    general.grid_protection_configured = True
    general.grid_protection_active = True
    general.grid_protection_timestamp = None
    monkeypatch.setattr(chargepoint_module, "Pub", Mock(return_value=duo.mqtt))
    monkeypatch.setattr(data.data.counter_all_data, "get_evu_counter", Mock(return_value=Mock()))
    monkeypatch.setattr(chargepoint_module.chargelog, "save_and_reset_data",
                        Mock(side_effect=lambda cp, ev: cp.reset_log_data()))
    ocpp_client = Mock()
    ocpp_client.is_unlock_in_progress.return_value = False
    monkeypatch.setattr(data.data, "ocpp_client", ocpp_client)
    for cp in duo.chargepoints:
        cp.data.get.plug_state = True
        cp.data.set.plug_state_prev = True
        cp.data.set.rfid = rfid_tag
        cp.data.set.manual_lock = False
        cp.data.set.plug_time = duo.clock.return_value - 60
        cp.data.set.log.imported_at_plugtime = 1000
        cp.data.get.imported = 1100
    unplugged.data.get.plug_state = False
    unplugged.data.get.charge_state = stale_charge_state
    unplugged.data.config.ocpp_chargebox_id = "duo-unplugged"
    unplugged.data.get.ocpp.transaction_id = 42
    unplugged.chargepoint_module.fault_state = 0
    duo.reader.scan("ABC")
    order = list(reversed(duo.chargepoints)) if reverse_order else duo.chargepoints

    for cp in order:
        cp.update(data.data.ev_data)

    ocpp_client.request_stop.assert_called_once_with(
        chargebox_id=unplugged.data.config.ocpp_chargebox_id,
        imported=1100,
        id_tag=rfid_tag,
        reason="EVDisconnected",
    )
    # Der asynchrone Coordinator löscht die ID erst nach bestätigtem Stop.
    assert unplugged.data.get.ocpp.transaction_id == 42
    assert unplugged.data.set.rfid is None
    assert unplugged.data.get.rfid == "ABC"
    assert unplugged.data.get.rfid_timestamp == duo.clock.return_value
    assert partner.data.set.rfid == rfid_tag
    assert partner.data.get.rfid is None
    assert all(cp.chargepoint_module.clear_rfid.call_count == 0 for cp in duo.chargepoints)
    assert not [record for record in caplog.records if record.levelno >= 40]

    duo.clock.return_value += 60
    unplugged.data.get.ocpp.transaction_id = None
    unplugged.data.get.charge_state = False
    unplugged.data.get.plug_state = True
    unplugged.data.set.plug_time = duo.clock.return_value
    for cp in order:
        cp._validate_rfid()
        if cp.data.get.rfid is not None and cp.data.get.plug_state:
            cp._link_rfid_to_cp()
    assert unplugged.data.set.rfid == "ABC"
    assert partner.data.set.rfid == rfid_tag
    assert all(cp.data.get.rfid is None for cp in duo.chargepoints)
    assert sum(cp.chargepoint_module.clear_rfid.call_count for cp in duo.chargepoints) == 1


@pytest.mark.parametrize("selected_index", [0, 1])
@pytest.mark.parametrize("committed", [False, True])
def test_ocpp_start_uses_only_assigned_duo_tag(duo, rfid_tag, selected_index, committed, monkeypatch):
    cp = duo.chargepoints[selected_index]
    cp.data.config.ocpp_chargebox_id = "duo-selected"
    cp.data.get.ocpp.connected = True
    cp.data.get.plug_state = True
    cp.data.get.rfid = "ABC"
    cp.data.set.rfid = rfid_tag if committed else None
    data.data.optional_data.data.ocpp.config.active = True
    ocpp_client = Mock()
    monkeypatch.setattr(data.data, "ocpp_client", ocpp_client)

    cp._process_ocpp_start()

    if committed:
        ocpp_client.request_start.assert_called_once_with(
            chargebox_id="duo-selected", connector_id=1, id_tag=rfid_tag, imported=cp.data.get.imported)
    else:
        ocpp_client.request_start.assert_not_called()
    assert cp.data.get.rfid == "ABC"


@pytest.fixture
def remote_duo(duo, monkeypatch):
    data.data.optional_data.data.ocpp.config.active = True
    general = data.data.general_data.data
    general.grid_protection_configured = True
    general.grid_protection_active = True
    general.grid_protection_timestamp = None
    client = Mock()
    client.is_unlock_in_progress.return_value = False
    monkeypatch.setattr(data.data, "ocpp_client", client)
    monkeypatch.setattr(data.data.counter_all_data, "get_evu_counter", Mock(return_value=Mock()))
    monkeypatch.setattr(chargepoint_module.chargelog, "save_and_reset_data",
                        Mock(side_effect=lambda cp, ev: cp.reset_log_data()))
    monkeypatch.setattr(chargepoint_module, "Pub", Mock(return_value=duo.mqtt))
    monkeypatch.setattr(chargepoint_module, "create_timestamp", duo.clock)
    monkeypatch.setattr(ocpp_chargepoint, "create_timestamp", duo.clock)
    for cp in duo.chargepoints:
        cp.data.config.ocpp_chargebox_id = f"duo-{cp.num}"
        cp.data.get.ocpp.connected = True

    models = {f"cp{point.num}": SimpleNamespace(chargepoint=point) for point in duo.chargepoints}
    monkeypatch.setattr(SubData, "cp_data", models)

    def deliver(cp, suffix, payload):
        message = SimpleNamespace(topic=f"openWB/chargepoint/{cp.num}/get/{suffix}",
                                  payload=json.dumps(payload).encode())
        SubData.process_chargepoint_topic(object.__new__(SubData), models, message)

    def publish(topic, payload):
        cp = next(point for point in duo.chargepoints if f"/chargepoint/{point.num}/" in topic)
        deliver(cp, topic.split("/get/", 1)[1], payload)

    remote_mqtt = Mock()
    remote_mqtt.pub.side_effect = publish
    monkeypatch.setattr(ocpp_chargepoint, "Pub", Mock(return_value=remote_mqtt))

    def request(cp, tag):
        async def send_request():
            handler = OcppChargePoint(cp.data.config.ocpp_chargebox_id, AsyncMock())
            return await handler.remote_start_transaction(tag, 1)
        return asyncio.run(send_request()).status

    def run(reverse_order=False):
        order = list(reversed(duo.chargepoints)) if reverse_order else duo.chargepoints
        for cp in order:
            cp.update(data.data.ev_data)

    hardware_messages = Mock()

    def hardware(cp, tag, timestamp, after_message=None):
        def send(topic, payload, digits=None):
            publish(topic, payload)
            if after_message is not None:
                after_message(topic, payload)
        hardware_messages.side_effect = send
        store = chargepoint_store.ChargepointValueStoreBroker(cp.num)
        store.set(ChargepointState(
            rfid=tag, rfid_timestamp=timestamp,
            plug_state=cp.data.get.plug_state, charge_state=cp.data.get.charge_state,
            imported=cp.data.get.imported, exported=0, power=0,
            currents=[0, 0, 0], phases_in_use=1))
        store.update()

    monkeypatch.setattr(chargepoint_store, "pub_to_broker", hardware_messages)
    return SimpleNamespace(duo=duo, request=request, run=run, deliver=deliver, client=client,
                           hardware=hardware, hardware_messages=hardware_messages)


@pytest.fixture
def active_ocpp_duo(remote_duo):
    setup = remote_duo
    client = setup.client
    client._rfid_authorize_pending = {}
    for name in ("authorize_for_rfid", "finish_rfid_authorization", "discard_rfid_authorization"):
        setattr(client, name, MethodType(getattr(OcppClient, name), client))
    futures = {}

    def authorize(chargebox_id, id_tag):
        future = concurrent.futures.Future()
        futures[chargebox_id] = future
        return future

    client.authorize.side_effect = authorize
    client.request_stop.return_value = None
    for cp in setup.duo.chargepoints:
        cp.data.get.plug_state = True
        cp.data.set.plug_state_prev = True
        cp.data.get.charge_state = True
        cp.data.set.rfid = "04A1B2C3D4"
        cp.data.set.rfid_timestamp = setup.duo.clock.return_value - 60
        cp.data.get.ocpp.transaction_id = cp.num
        cp.data.get.ocpp.transaction_id_tag = cp.data.set.rfid
        cp.data.get.ocpp.tag_accepted = True
    setup.futures = futures
    return setup


@pytest.mark.parametrize("ocpp_indices", [(0, 1), (0,), (1,)])
@pytest.mark.parametrize("reverse_order", [False, True])
@pytest.mark.parametrize("accepted", [False, True])
def test_duo_authorization_during_charging_keeps_scan_until_backend_reply(
        active_ocpp_duo, ocpp_indices, reverse_order, accepted):
    setup = active_ocpp_duo
    points = setup.duo.chargepoints
    for index, cp in enumerate(points):
        if index not in ocpp_indices:
            cp.data.config.ocpp_chargebox_id = None
            cp.data.get.ocpp.transaction_id = None
    setup.duo.reader.scan("ABC", setup.duo.clock.return_value)
    setup.run(reverse_order)
    expected_boxes = {points[index].data.config.ocpp_chargebox_id for index in ocpp_indices}
    assert set(setup.futures) == expected_boxes
    assert setup.client.authorize.call_count == len(ocpp_indices)
    setup.client.request_stop.assert_not_called()
    for index in ocpp_indices:
        assert points[index].data.get.rfid == "ABC"
        assert points[index].data.get.ocpp.authorization_flow_status == "init"

    # Jeder Ladepunkt muss auch bei unterschiedlich spaeten Antworten unabhaengig abschliessen.
    for index in ocpp_indices:
        cp = points[index]
        setup.futures[cp.data.config.ocpp_chargebox_id].set_result(SimpleNamespace(accepted=accepted))
        for point in points:
            point.data.get.state_str = None
        setup.run(reverse_order)
        expected_word = "akzeptiert" if accepted else "abgelehnt"
        assert f"ID-Tag ABC wurde vom OCPP-Server {expected_word}." in cp.data.get.state_str
        assert "Beide Ladepunkte" not in cp.data.get.state_str
        assert cp.data.get.rfid is None
        for pending_index in ocpp_indices:
            pending = points[pending_index]
            if not setup.futures[pending.data.config.ocpp_chargebox_id].done():
                assert pending.data.get.rfid == "ABC"
                assert pending.data.get.ocpp.authorization_flow_status == "init"
    for cp in points:
        assert cp.data.set.rfid == "04A1B2C3D4"
        assert cp.data.config.ev == 0
    assert setup.client._rfid_authorize_pending == {}
    assert setup.client.authorize.call_count == len(ocpp_indices)
    setup.client.request_stop.assert_not_called()


@pytest.mark.parametrize("ocpp_indices", [(0, 1), (0,), (1,)])
@pytest.mark.parametrize("reverse_order", [False, True])
def test_duo_same_tag_requests_stop_for_each_ocpp_transaction(
        active_ocpp_duo, ocpp_indices, reverse_order):
    setup = active_ocpp_duo
    for index, cp in enumerate(setup.duo.chargepoints):
        if index not in ocpp_indices:
            cp.data.config.ocpp_chargebox_id = None
            cp.data.get.ocpp.transaction_id = None
    setup.duo.reader.scan("04A1B2C3D4", setup.duo.clock.return_value)
    setup.run(reverse_order)
    setup.run(reverse_order)
    assert {entry.kwargs["chargebox_id"] for entry in setup.client.request_stop.call_args_list} == {
        setup.duo.chargepoints[index].data.config.ocpp_chargebox_id for index in ocpp_indices}
    assert setup.client.request_stop.call_count == len(ocpp_indices)
    assert all(entry.kwargs["authorize_stop"] is True for entry in setup.client.request_stop.call_args_list)
    setup.client.authorize.assert_not_called()


@pytest.mark.parametrize("running_index", [0, 1])
@pytest.mark.parametrize("reverse_order", [False, True])
def test_duo_assignment_at_free_partner_preserves_running_authorization(
        active_ocpp_duo, running_index, reverse_order):
    setup = active_ocpp_duo
    running = setup.duo.chargepoints[running_index]
    free = setup.duo.chargepoints[1 - running_index]
    free.data.get.ocpp.transaction_id = None
    free.data.get.ocpp.transaction_id_tag = None
    free.data.get.ocpp.tag_accepted = False
    free.data.get.charge_state = False
    free.data.set.rfid = None
    setup.duo.reader.scan("ABC", setup.duo.clock.return_value)
    setup.run(reverse_order)
    assert free.data.set.rfid == "ABC"
    assert running.data.set.rfid == "04A1B2C3D4"
    assert running.data.get.rfid == "ABC"
    assert running.data.get.ocpp.authorization_flow_status == "init"
    setup.futures[running.data.config.ocpp_chargebox_id].set_result(SimpleNamespace(accepted=True))
    running.data.get.state_str = None
    setup.run(reverse_order)
    assert "ID-Tag ABC wurde vom OCPP-Server akzeptiert." in running.data.get.state_str
    assert running.data.set.rfid == "04A1B2C3D4"
    setup.client.request_stop.assert_not_called()


def test_background_copy_does_not_clear_invalid_scan_during_duo_transaction(active_ocpp_duo):
    setup = active_ocpp_duo
    setup.duo.reader.scan("UNKNOWN", setup.duo.clock.return_value)
    cp = setup.duo.chargepoints[0]
    copied = copy.deepcopy(cp)
    copied._validate_rfid()
    assert cp.data.get.rfid == "UNKNOWN"
    setup.duo.mqtt.pub.assert_not_called()
    cp.chargepoint_module.clear_rfid.assert_not_called()
    cp._validate_rfid()
    assert cp.data.get.rfid is None
    assert "keinem Ladepunkt-Profil oder Fahrzeug zugeordnet" in cp.data.get.state_str
    assert setup.duo.chargepoints[1].data.get.rfid == "UNKNOWN"


@pytest.mark.parametrize("target_index", [0, 1])
@pytest.mark.parametrize("reverse_order", [False, True])
@pytest.mark.parametrize("remote_tag", ["ABC", "04A1B2C3D4"])
def test_remote_start_discards_local_scan_and_uses_fixed_duo_target(
        remote_duo, rfid_tag, target_index, reverse_order, remote_tag, caplog):
    setup = remote_duo
    duo = setup.duo
    remote = duo.chargepoints[target_index]
    local = duo.chargepoints[1 - target_index]
    scanned_at = duo.clock.return_value
    duo.reader.scan(rfid_tag, scanned_at)
    # Ein erster Regelzyklus hält den gemeinsamen Scan an beiden leeren LP vorläufig.
    setup.run(reverse_order)
    duo.clock.return_value += 60
    assert setup.request(remote, remote_tag) == RemoteStartStopStatus.accepted
    setup.run(reverse_order)
    assert local.data.get.rfid is None
    assert local.data.get.rfid_timestamp is None
    assert remote.data.get.rfid == remote_tag
    assert remote.data.get.ocpp.remote_start
    assert all(cp.data.set.rfid is None for cp in duo.chargepoints)
    assert remote.data.set.rfid_timestamp == scanned_at
    remote.chargepoint_module.clear_rfid.assert_called_once_with()

    # Beide Autos stecken: nur das angesprochene Ziel bekommt den Remote-Tag.
    local.data.get.plug_state = remote.data.get.plug_state = True
    local.data.set.plug_time = scanned_at - 20
    remote.data.set.plug_time = scanned_at - 10
    setup.client.request_start.reset_mock()
    setup.run(reverse_order)
    assert local.data.set.rfid is None
    assert remote.data.set.rfid == remote_tag
    assert remote.data.set.rfid_timestamp == duo.clock.return_value
    assert remote.data.get.ocpp.remote_start is False
    assert remote.chargepoint_module.clear_rfid.call_count == 1
    local.chargepoint_module.clear_rfid.assert_not_called()
    assert {entry.kwargs["chargebox_id"]: entry.kwargs["id_tag"]
            for entry in setup.client.request_start.call_args_list} == {
                remote.data.config.ocpp_chargebox_id: remote_tag,
            }
    assert not [record for record in caplog.records if record.levelno >= 40]


@pytest.mark.parametrize("target_index", [0, 1])
@pytest.mark.parametrize("reverse_order", [False, True])
def test_remote_start_discards_partner_scan_and_allows_rescan(remote_duo, rfid_tag, target_index, reverse_order):
    setup = remote_duo
    duo = setup.duo
    remote = duo.chargepoints[target_index]
    local = duo.chargepoints[1 - target_index]
    local.data.get.rfid = rfid_tag
    local.data.get.rfid_timestamp = duo.clock.return_value
    duo.clock.return_value += 60
    assert setup.request(remote, "ABC") == RemoteStartStopStatus.accepted
    remote.data.get.plug_state = True
    setup.run(reverse_order)
    assert remote.data.set.rfid == "ABC"
    assert remote.data.set.rfid_timestamp == duo.clock.return_value
    assert local.data.get.rfid is None
    local.chargepoint_module.clear_rfid.assert_called_once_with()
    local.data.get.plug_state = True
    setup.duo.clock.return_value += 1
    setup.hardware(local, rfid_tag, setup.duo.clock.return_value)
    setup.run(reverse_order)
    assert local.data.set.rfid == rfid_tag


@pytest.mark.parametrize("outcome", ["timeout", "local_rejection", "backend_rejection"])
def test_remote_start_rejection_and_timeout_do_not_acknowledge_shared_reader(remote_duo, outcome):
    setup = remote_duo
    cp, partner = setup.duo.chargepoints
    assert setup.request(cp, "ABC") == RemoteStartStopStatus.accepted
    cp.chargepoint_module.clear_rfid.reset_mock()
    partner.data.get.rfid = "ABC"
    partner.data.get.rfid_timestamp = setup.duo.clock.return_value
    if outcome == "timeout":
        setup.duo.clock.return_value += 301
    elif outcome == "local_rejection":
        cp.template.data.valid_tags = []
    else:
        cp.data.get.ocpp.authorization_flow_status = "rejected"
    cp._process_ocpp_rfid()
    cp._validate_rfid()
    assert cp.data.get.rfid is None
    assert cp.data.get.rfid_timestamp is None
    assert cp.data.get.ocpp.remote_start is False
    assert cp.data.set.rfid_timestamp is None
    assert partner.data.get.rfid == "ABC"
    cp.chargepoint_module.clear_rfid.assert_not_called()
    setup.client.request_start.assert_not_called()


def test_remote_start_keeps_existing_partner_assignment(remote_duo):
    setup = remote_duo
    cp, partner = setup.duo.chargepoints
    partner.data.set.rfid = "ASSIGNED"
    partner.data.get.plug_state = True
    partner.data.get.charge_state = True
    setup.duo.reader.scan("04A1B2C3D4", setup.duo.clock.return_value)
    assert setup.request(cp, "ABC") == RemoteStartStopStatus.accepted
    assert partner.data.set.rfid == "ASSIGNED"
    assert partner.data.get.rfid is None
    assert cp.data.get.rfid == "ABC"
    cp.chargepoint_module.clear_rfid.assert_called_once_with()


@pytest.mark.parametrize("reason", ["invalid_tag", "busy"])
def test_rejected_remote_start_does_not_discard_local_scan(remote_duo, reason):
    setup = remote_duo
    cp, partner = setup.duo.chargepoints
    setup.duo.reader.scan("04A1B2C3D4", setup.duo.clock.return_value)
    if reason == "busy":
        cp.data.get.charge_state = True
    tag = "UNKNOWN" if reason == "invalid_tag" else "ABC"
    assert setup.request(cp, tag) == RemoteStartStopStatus.rejected
    assert cp.data.get.rfid == partner.data.get.rfid == "04A1B2C3D4"
    for point in setup.duo.chargepoints:
        point.chargepoint_module.clear_rfid.assert_not_called()


def test_reader_scan_without_timestamp_does_not_reuse_remote_timestamp(remote_duo):
    setup = remote_duo
    cp = setup.duo.chargepoints[0]
    assert setup.request(cp, "ABC") == RemoteStartStopStatus.accepted
    setup.hardware(cp, "04A1B2C3D4", None)
    assert cp.data.get.rfid_timestamp is None
    assert cp.data.get.rfid == "04A1B2C3D4"
    assert cp.data.get.ocpp.remote_start is False


@pytest.mark.parametrize("same_tag", [False, True])
def test_new_reader_scan_replaces_remote_origin(remote_duo, same_tag):
    setup = remote_duo
    cp = setup.duo.chargepoints[0]
    assert setup.request(cp, "ABC") == RemoteStartStopStatus.accepted
    setup.duo.clock.return_value += 1
    tag = "ABC" if same_tag else "04A1B2C3D4"

    def check_transition(topic, payload):
        if topic.endswith("/rfid_timestamp"):
            assert cp.data.get.rfid is None
            assert cp.data.get.ocpp.remote_start is False
    setup.hardware(cp, tag, setup.duo.clock.return_value, check_transition)
    assert cp.data.get.ocpp.remote_start is False
    assert cp.data.get.rfid == tag
    assert cp.data.get.rfid_timestamp == setup.duo.clock.return_value


def test_discarded_scan_cannot_be_reused_after_remote_start(remote_duo):
    setup = remote_duo
    cp = setup.duo.chargepoints[0]
    timestamp = setup.duo.clock.return_value
    setup.duo.reader.scan("04A1B2C3D4", timestamp)
    setup.duo.clock.return_value += 60
    assert setup.request(cp, "ABC") == RemoteStartStopStatus.accepted
    setup.hardware(cp, "04A1B2C3D4", timestamp)
    cp._validate_rfid()
    assert cp.data.get.rfid is None
    assert cp.data.set.rfid is None
    assert cp.data.set.rfid_timestamp == timestamp


@pytest.mark.parametrize("tag", [None, ""])
def test_incomplete_hardware_scan_preserves_remote_start(remote_duo, tag):
    setup = remote_duo
    cp = setup.duo.chargepoints[0]
    assert setup.request(cp, "ABC") == RemoteStartStopStatus.accepted
    setup.hardware(cp, tag, setup.duo.clock.return_value + 1)
    assert cp.data.get.ocpp.remote_start is True
    assert cp.data.get.rfid == "ABC"


@pytest.mark.parametrize("timestamp", [None, 1700000000])
def test_hardware_scan_without_remote_start_is_forwarded(remote_duo, timestamp):
    setup = remote_duo
    cp = setup.duo.chargepoints[0]
    setup.hardware(cp, "ABC", timestamp)
    assert cp.data.get.rfid == "ABC"
    assert cp.data.get.rfid_timestamp == timestamp
    assert cp.data.get.ocpp.remote_start is False


def test_hardware_scan_replaces_remote_start_without_timestamp_comparison(remote_duo):
    setup = remote_duo
    cp = setup.duo.chargepoints[0]
    assert setup.request(cp, "ABC") == RemoteStartStopStatus.accepted
    setup.hardware(cp, "04A1B2C3D4", setup.duo.clock.return_value - 60)
    assert cp.data.get.rfid == "04A1B2C3D4"
    assert cp.data.get.ocpp.remote_start is False


@pytest.mark.parametrize("reverse_order", [False, True])
def test_new_hardware_scan_waits_for_tag_between_messages(remote_duo, reverse_order):
    setup = remote_duo
    cp = setup.duo.chargepoints[0]
    assert setup.request(cp, "ABC") == RemoteStartStopStatus.accepted
    cp.data.get.plug_state = True

    def check_transition(topic, payload):
        if topic.endswith(("/ocpp/remote_start", "/rfid_timestamp")):
            setup.run(reverse_order)
            assert cp.data.set.rfid is None

    setup.hardware(cp, "04A1B2C3D4", setup.duo.clock.return_value + 1, check_transition)
    setup.run(reverse_order)
    assert cp.data.set.rfid == "04A1B2C3D4"


@pytest.mark.parametrize("reverse_order", [False, True])
def test_remote_start_waits_for_tag_after_separate_origin_and_timestamp(remote_duo, reverse_order):
    setup = remote_duo
    cp, partner = setup.duo.chargepoints
    cp.data.get.plug_state = True
    cp.data.get.rfid = partner.data.get.rfid = "04A1B2C3D4"
    cp.data.get.rfid_timestamp = partner.data.get.rfid_timestamp = setup.duo.clock.return_value - 60
    cp._clear_pending_rfid(cp.data.get.rfid, partner)
    setup.deliver(cp, "rfid", None)
    setup.deliver(cp, "ocpp/remote_start", True)
    assert cp.data.get.ocpp.remote_start is True
    assert cp.data.get.rfid is None
    setup.run(reverse_order)
    setup.deliver(cp, "rfid_timestamp", setup.duo.clock.return_value)
    setup.run(reverse_order)
    assert cp.data.set.rfid is None
    assert partner.data.get.rfid is None
    setup.deliver(cp, "rfid", "ABC")
    setup.run(reverse_order)
    assert cp.data.set.rfid == "ABC"
    assert cp.data.get.ocpp.remote_start is False
    assert partner.data.get.rfid is None
    cp.chargepoint_module.clear_rfid.assert_called_once_with()


@pytest.mark.parametrize("value", [True, False, {"id_tag": "ABC", "timestamp": 123}])
def test_remote_start_mqtt_uses_boolean_validation(monkeypatch, value):
    mqtt = Mock()
    monkeypatch.setattr(setdata, "Pub", Mock(return_value=mqtt))
    monkeypatch.setattr(SubData, "cp_data", {"cp1": Mock()})
    topic = "openWB/set/chargepoint/1/get/ocpp/remote_start"
    message = SimpleNamespace(topic=topic, payload=json.dumps(value).encode())
    setdata.SetData.process_chargepoint_topic(object.__new__(setdata.SetData), message)
    forwarded = [entry for entry in mqtt.pub.call_args_list
                 if entry.args[0] == "openWB/chargepoint/1/get/ocpp/remote_start"]
    if isinstance(value, bool):
        assert len(forwarded) == 1
        assert forwarded[0].args[1] is value
    else:
        assert forwarded == []


@pytest.mark.parametrize("case", ["wildcard", "vehicle", "locked_vehicle", "invalid",
                                  "assigned", "pending", "charging", "local_scan"])
def test_remote_start_checks_target_permissions_and_preserves_existing_state(remote_duo, rfid_tag, case):
    setup = remote_duo
    cp = setup.duo.chargepoints[0]
    tag = rfid_tag
    expected = RemoteStartStopStatus.rejected
    if case == "wildcard":
        cp.template.data.valid_tags = ["REMOTE-*"]
        tag = "REMOTE-123"
        expected = RemoteStartStopStatus.accepted
    elif case in ("vehicle", "locked_vehicle"):
        cp.template.data.valid_tags = []
        next(iter(data.data.ev_data.values())).data.tag_id = [tag]
        cp.data.set.manual_lock = case == "locked_vehicle"
        if case == "vehicle":
            expected = RemoteStartStopStatus.accepted
    elif case == "invalid":
        tag = "UNKNOWN"
    elif case == "assigned":
        cp.data.set.rfid = "ABC"
    elif case == "pending":
        assert setup.request(cp, "ABC") == RemoteStartStopStatus.accepted
    elif case == "charging":
        cp.data.get.charge_state = True
    else:
        cp.data.get.rfid = "ABC"
        cp.data.get.rfid_timestamp = setup.duo.clock.return_value
        expected = RemoteStartStopStatus.accepted
    old_tag = cp.data.get.rfid
    old_assignment = cp.data.set.rfid
    assert setup.request(cp, tag) == expected
    if expected == RemoteStartStopStatus.rejected:
        assert cp.data.get.rfid == old_tag
        assert cp.data.set.rfid == old_assignment
    else:
        cp.data.get.plug_state = True
        setup.run()
        assert cp.data.set.rfid == tag
    if expected == RemoteStartStopStatus.accepted or case == "pending":
        cp.chargepoint_module.clear_rfid.assert_called_once_with()
    else:
        cp.chargepoint_module.clear_rfid.assert_not_called()


@pytest.mark.parametrize("unplugged_index", [0, 1])
def test_duo_unplugging_clears_only_own_assignment_and_allows_new_card(
        duo, rfid_tag, unplugged_index, monkeypatch):
    cp = duo.chargepoints[unplugged_index]
    partner = duo.chargepoints[1 - unplugged_index]
    for point in duo.chargepoints:
        point.data.get.plug_state = True
        point.data.set.plug_state_prev = True
        point.data.set.rfid = rfid_tag
        point.data.set.manual_lock = False
        point.data.set.plug_time = duo.clock.return_value - 60
    monkeypatch.setattr(data.data.counter_all_data, "get_evu_counter", Mock(return_value=Mock()))
    monkeypatch.setattr(chargepoint_module, "Pub", Mock(return_value=duo.mqtt))
    monkeypatch.setattr(chargepoint_module.chargelog, "save_and_reset_data",
                        Mock(side_effect=lambda point, ev: point.reset_log_data()))
    cp.data.get.plug_state = False

    cp._process_charge_stop()

    assert cp.data.set.rfid is None
    assert cp.data.set.plug_time is None
    assert cp.data.set.manual_lock is True
    assert partner.data.set.rfid == rfid_tag
    assert partner.data.set.manual_lock is False
    duo.reader.scan("ABC")
    for point in duo.chargepoints:
        point._validate_rfid()
    assert cp.data.get.rfid == "ABC"
    assert partner.data.get.rfid is None
    cp.data.get.plug_state = True
    cp.data.set.plug_time = duo.clock.return_value + 10
    duo.clock.return_value += 10
    cp._validate_rfid()
    cp._link_rfid_to_cp()
    assert cp.data.set.rfid == "ABC"
    assert partner.data.set.rfid == rfid_tag


@pytest.mark.parametrize("target_index", [0, 1])
@pytest.mark.parametrize("reverse_order", [False, True])
@pytest.mark.parametrize("scan_before_plug", [False, True])
def test_duo_vehicle_tag_without_chargepoint_permission_leaves_slot_available_for_new_tag(
        duo, target_index, reverse_order, scan_before_plug):
    """Eine EV-Zuordnung allein darf einen gesperrten LP nicht dauerhaft belegen."""
    target = duo.chargepoints[target_index]
    other = duo.chargepoints[1 - target_index]
    ev = Ev(9)
    ev.data.tag_id = ["NUR-ANDERER-LP"]
    data.data.ev_data["ev9"] = ev
    other.template.data.valid_tags.append("NUR-ANDERER-LP")
    order = list(reversed(duo.chargepoints)) if reverse_order else duo.chargepoints
    if scan_before_plug:
        duo.reader.scan("NUR-ANDERER-LP")
        for cp in order:
            cp._validate_rfid()
        for cp in duo.chargepoints:
            cp.data.get.plug_state = True
            cp.data.set.plug_time = duo.clock.return_value + (10 if cp is target else 20)
        duo.clock.return_value += 30
    else:
        for cp in duo.chargepoints:
            cp.data.get.plug_state = True
            cp.data.set.plug_time = duo.clock.return_value - (10 if cp is target else 20)
        duo.reader.scan("NUR-ANDERER-LP")
    for cp in order:
        cp._validate_rfid()
        if cp.data.get.rfid is not None:
            cp._link_rfid_to_cp()
    assert all(cp.data.set.rfid is None for cp in duo.chargepoints)
    assert all(cp.data.set.manual_lock for cp in duo.chargepoints)
    if scan_before_plug:
        # Ohne eindeutige zeitliche Zuordnung bleibt der Scan vorläufig erhalten.
        assert all(cp.data.get.rfid == "NUR-ANDERER-LP" for cp in duo.chargepoints)
        assert all(cp.data.set.rfid_timestamp is None for cp in duo.chargepoints)
    else:
        assert all(cp.data.get.rfid is None for cp in duo.chargepoints)
        assert "nicht gültig" in target.data.get.state_str

    # Weder ein abgelehnter noch ein zeitlich unklarer Scan belegt einen Platz.
    duo.clock.return_value += 1
    duo.reader.scan("ABC", duo.clock.return_value)
    for _ in range(2):
        for cp in order:
            cp._validate_rfid()
            if cp.data.get.rfid is not None:
                cp._link_rfid_to_cp()
            cp.is_charging_possible()
    # Beim zweiten Scan stecken beide bereits: jetzt gilt die letzte Einsteckzeit.
    expected = other if scan_before_plug else target
    assert expected.data.set.rfid == "ABC"
    assert expected.data.set.manual_lock is False
    assert sum(cp.data.set.rfid is not None for cp in duo.chargepoints) == 1
