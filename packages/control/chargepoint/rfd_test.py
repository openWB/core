import copy
from types import SimpleNamespace

from control import prepare
from control.chargepoint import chargepoint as chargepoint_module
from control.chargepoint import rfid

from typing import Optional
from unittest.mock import Mock

import pytest
from control import data
from control.chargepoint.chargepoint import Chargepoint
from control.chargepoint.chargepoint_template import CpTemplate
from control.ev.ev import Ev


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

    def scan(tag):
        # Der gemeinsame Leser meldet denselben Scan an beide Duo-Ladepunkte.
        for cp in chargepoints:
            cp.data.get.rfid = tag

    reader = Mock(name="rfid_reader", spec=["scan"])
    reader.scan.side_effect = scan
    return SimpleNamespace(chargepoints=chargepoints, reader=reader, mqtt=mqtt, clock=clock)


@pytest.fixture
def duo_regelzyklus(duo, rfid_tag, monkeypatch, caplog):
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
def test_duo_partner_wird_erkannt(duo, module_type):
    for cp in duo.chargepoints:
        cp.data.config.type = module_type
    cp1, cp2 = duo.chargepoints
    assert cp1.find_duo_partner() == cp2.num
    assert cp2.find_duo_partner() == cp1.num


@pytest.mark.parametrize("plugged_index", [0, 1], ids=["Ladepunkt-1", "Ladepunkt-2"])
@pytest.mark.parametrize("reverse_order", [False, True], ids=["Reihenfolge-1-2", "Reihenfolge-2-1"])
def test_scan_wird_nur_dem_eingesteckten_ladepunkt_zugeordnet(
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
def test_scan_zeitlimit_ohne_auto(duo, duo_regelzyklus, rfid_tag, elapsed):
    default_ev = duo_regelzyklus.default_ev
    duo.reader.scan(rfid_tag)
    duo_regelzyklus.run()
    assert all(cp.data.get.connected_vehicle.info.id == duo_regelzyklus.tagged_ev.num
               for cp in duo.chargepoints)
    duo.clock.return_value += elapsed
    duo_regelzyklus.run()

    for cp in duo.chargepoints:
        assert cp.data.set.rfid is None
        assert cp.data.get.plug_state is False
        assert cp.data.set.manual_lock is True
        if elapsed == 300:
            assert cp.data.get.rfid == rfid_tag
            assert cp.data.get.rfid_timestamp == duo.clock.return_value - elapsed
            assert cp.data.get.connected_vehicle.info.id == duo_regelzyklus.tagged_ev.num
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
def test_produktionsschleife_reset_spaetestens_im_folgezyklus(
        duo, duo_regelzyklus, rfid_tag, plugged_index, reverse_order):
    """Eine vorläufige Anzeige darf höchstens bis zum Folgezyklus bestehen."""
    order = list(reversed(duo.chargepoints)) if reverse_order else duo.chargepoints
    data.data.cp_data = {f"cp{cp.num}": cp for cp in order}
    plugged = duo.chargepoints[plugged_index]
    other = duo.chargepoints[1 - plugged_index]
    duo.reader.scan(rfid_tag)
    duo_regelzyklus.run()
    assert all(cp.data.get.connected_vehicle.info.id == 1 for cp in duo.chargepoints)

    duo.clock.return_value += 60
    plugged.data.get.plug_state = True
    duo_regelzyklus.run()
    first_cycle_id = other.data.get.connected_vehicle.info.id
    assert other.data.get.rfid is None
    assert other.data.config.ev == 0
    # Ein unmittelbarer Reset ist ebenfalls zulässig. Entscheidend ist der
    # garantierte Reset im Folgezyklus, nicht eine bestimmte alte Verzögerung.
    assert first_cycle_id in (duo_regelzyklus.default_ev.num, duo_regelzyklus.tagged_ev.num)

    duo_regelzyklus.run()
    next_cycle_id = other.data.get.connected_vehicle.info.id
    assert next_cycle_id == 0, "Fahrzeug bleibt auch im Folgezyklus am freien LP zugeordnet."
    assert plugged.data.get.connected_vehicle.info.id == 1


@pytest.mark.parametrize("duo_mode, reverse_order", [(False, False), (True, False), (True, True)],
                         ids=["Einzel-LP", "Duo-LP1-LP2", "Duo-LP2-LP1"])
@pytest.mark.parametrize("assigned", [False, True], ids=["Ohne-RFID-Zuordnung", "Mit-RFID-Zuordnung"])
def test_neuer_scan_nach_ladestart_behaelt_bestehende_zuordnung(
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
def test_duo_rfid_freigabe_nur_am_zugeordneten_ladepunkt(
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
def test_rfid_freigabe_bleibt_erhalten(duo, rfid_tag, duo_mode, source):
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
def test_duo_rfid_gleichstand_fehlende_zeiten_warten(duo, rfid_tag, plug_times, reverse_order):
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
def test_duo_rfid_quittierung_gemeinsamer_leser(duo, rfid_tag, source_index):
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
def test_timeout_reset_duo_beachtet_beide_fahrzeugprofile(
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
def test_duo_energiepruefung_verwendet_ziel_statt_aufrufenden_ladepunkt(
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
def test_duo_ladender_lp_ohne_zaehlerfortschritt_scan_wartet_am_freien_partner(
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
def test_neuauswahl_nur_am_einzel_lp_duo_behaelt_erfolgreiche_zuordnung(
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
def test_duo_beide_zugeordnet_neuer_scan_aendert_nichts(
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
def test_scan_verwerfen_und_meldungen_nur_an_verfuegbaren_lps(
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
def test_duo_zwei_wartende_autos_nacheinander_freigeben_ohne_energiebezug(
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
def test_duo_scan_vor_beiden_autos_erstes_auto_auch_bei_verzoegerter_verarbeitung(
        duo, rfid_tag, first_index, reverse_order):
    duo.reader.scan(rfid_tag)
    for cp in duo.chargepoints:
        cp._validate_rfid()
    scanned_at = duo.clock.return_value
    for index, cp in enumerate(duo.chargepoints):
        cp.data.get.plug_state = True
        cp.data.set.plug_time = scanned_at + (10 if index == first_index else 20)
    duo.clock.return_value += 30
    order = list(reversed(duo.chargepoints)) if reverse_order else duo.chargepoints
    for _ in range(2):
        for cp in order:
            cp._validate_rfid()
            if cp.data.get.rfid is not None:
                cp._link_rfid_to_cp()
    assert duo.chargepoints[first_index].data.set.rfid == rfid_tag
    assert duo.chargepoints[1 - first_index].data.set.rfid is None
    assert sum(cp.chargepoint_module.clear_rfid.call_count for cp in duo.chargepoints) == 1


@pytest.mark.parametrize(
    "plug_after", [299, 301, None], ids=["Vor-Frist", "Nach-Frist", "Zeit-fehlt"])
@pytest.mark.parametrize("plugged_index", [0, 1])
def test_duo_timeout_mit_eingestecktem_ziel(
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


def test_duo_echter_tag_eingang_neuer_tag_behaelt_laufende_frist(duo, rfid_tag):
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
def test_duo_hintergrundkopie_veraendert_keinen_globalen_scan(duo, rfid_tag, source_index, event):
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
def test_autolock_duo_nur_mit_zugeordnetem_tag(duo, rfid_tag, duo_mode, committed):
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
def test_duo_scan_im_absteckzyklus_bleibt_erhalten_und_ocpp_behaelt_alten_tag(
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
    stop_transaction = Mock()
    monkeypatch.setattr(data.data.optional_data, "stop_transaction", stop_transaction)
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
    unplugged.data.set.ocpp_transaction_id = 42
    unplugged.chargepoint_module.fault_state = 0
    duo.reader.scan("ABC")
    order = list(reversed(duo.chargepoints)) if reverse_order else duo.chargepoints

    for cp in order:
        cp.update(data.data.ev_data)

    stop_transaction.assert_called_once_with(
        unplugged.data.config.ocpp_chargebox_id, 0, 1100, 42, rfid_tag)
    assert unplugged.data.set.ocpp_transaction_id is None
    assert unplugged.data.set.rfid is None
    assert unplugged.data.get.rfid == "ABC"
    assert unplugged.data.get.rfid_timestamp == duo.clock.return_value
    assert partner.data.set.rfid == rfid_tag
    assert partner.data.get.rfid is None
    assert all(cp.chargepoint_module.clear_rfid.call_count == 0 for cp in duo.chargepoints)
    assert not [record for record in caplog.records if record.levelno >= 40]

    duo.clock.return_value += 60
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


@pytest.mark.parametrize("unplugged_index", [0, 1])
def test_duo_abstecken_loest_nur_eigene_zuordnung_und_erlaubt_neue_karte(
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
def test_duo_fahrzeug_tag_ohne_lp_berechtigung_belegt_keinen_platz_neuer_tag_moeglich(
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
    assert all(cp.data.get.rfid is None for cp in duo.chargepoints)
    assert "nicht gültig" in target.data.get.state_str

    # Vorher war der Scan ungültig, also bleibt der Platz für eine gültige Karte frei.
    duo.reader.scan("ABC")
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
