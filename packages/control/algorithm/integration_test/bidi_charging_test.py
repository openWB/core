import pytest
from unittest.mock import Mock

from control import data
from control import loadmanagement
from control.algorithm.algorithm import Algorithm
from control.chargemode import Chargemode


@pytest.fixture()
def bidi_cps():
    def _setup(*cps):
        for counter in ("counter0", "counter6"):
            data.data.counter_data[counter].data.set.raw_currents_left = [32]*3
            data.data.counter_data[counter].data.set.raw_exported_currents_left = [32]*3
            data.data.counter_data[counter].data.set.raw_power_left = 22000
            data.data.counter_data[counter].data.set.raw_exported_power_left = 22000
        for cp in cps:
            data.data.cp_data[cp].data.get.max_discharge_power = -11000
            data.data.cp_data[cp].data.get.max_charge_power = 11000
            data.data.cp_data[cp].data.get.phases_in_use = 3
            control_parameter = data.data.cp_data[cp].data.control_parameter
            control_parameter.min_current = data.data.cp_data[cp].data.set.charging_ev_data.ev_template.data.min_current
            control_parameter.phases = 3
            control_parameter.required_currents = [16]*3
            control_parameter.required_current = 16
            control_parameter.chargemode = Chargemode.SCHEDULED_CHARGING
            control_parameter.submode = Chargemode.BIDI_CHARGING
    return _setup


@pytest.mark.parametrize("grid_power, expected_current",
                         [pytest.param(-2000, 2.898550724637681, id="bidi charge"),
                          pytest.param(2000, -2.898550724637681, id="bidi discharge")])
def test_cp3_bidi(grid_power: float, expected_current: float, bidi_cps, all_cp_not_charging, monkeypatch):
    # setup
    bidi_cps("cp3")
    data.data.counter_data["counter0"].data.get.power = grid_power
    return_mock = Mock(return_value=True)
    mock_get_component_name_by_id = Mock(return_value="Garage")
    monkeypatch.setattr(loadmanagement, "get_component_name_by_id", mock_get_component_name_by_id)
    monkeypatch.setattr(
        data.data.cp_data["cp3"].data.set.charging_ev_data.charge_template, "bidi_charging_allowed", return_mock)

    # execution
    Algorithm().calc_current()

    # evaluation
    assert data.data.cp_data["cp3"].data.set.current == expected_current
    assert data.data.cp_data["cp4"].data.set.current == 0
    assert data.data.cp_data["cp5"].data.set.current == 0
    assert data.data.counter_data["counter0"].data.set.surplus_power_left == 0


def test_cp3_cp4_bidi_discharge(bidi_cps, all_cp_not_charging, monkeypatch):
    # setup
    bidi_cps("cp3", "cp4")
    data.data.counter_data["counter0"].data.get.power = 4000
    mock_get_component_name_by_id = Mock(return_value="Garage")
    monkeypatch.setattr(loadmanagement, "get_component_name_by_id", mock_get_component_name_by_id)

    # execution
    Algorithm().calc_current()

    # evaluation
    assert data.data.cp_data["cp3"].data.set.current == -2.898550724637681
    assert data.data.cp_data["cp4"].data.set.current == -2.898550724637681
    assert data.data.cp_data["cp5"].data.set.current == 0
    assert data.data.counter_data["counter0"].data.set.surplus_power_left == 0


def test_cp3_bidi_instant_discharge_uses_dc_current(bidi_cps, all_cp_not_charging, monkeypatch):
    # Testet, ob das Entladen entsprechend vom max_discharge_power limitiert wird

    # setup
    bidi_cps("cp3")
    control_parameter = data.data.cp_data["cp3"].data.control_parameter
    control_parameter.chargemode = Chargemode.INSTANT_CHARGING
    data.data.cp_data["cp3"].data.set.charging_ev_data.data.get.soc = 80
    data.data.cp_data["cp3"].data.set.charging_ev_data.charge_template.data.chargemode.instant_charging.dc_current = -20
    mock_get_component_name_by_id = Mock(return_value="Garage")
    monkeypatch.setattr(loadmanagement, "get_component_name_by_id", mock_get_component_name_by_id)

    # execution
    Algorithm().calc_current()

    # evaluation
    assert data.data.cp_data["cp3"].data.set.current == -15.942028985507246
    assert data.data.cp_data["cp4"].data.set.current == 0
    assert data.data.cp_data["cp5"].data.set.current == 0
    assert data.data.counter_data["counter0"].data.set.surplus_power_left == 10310.0


def test_cp3_bidi_instant_discharge_limited_by_counter_export_current(
        bidi_cps, all_cp_not_charging, monkeypatch):
    # Testet, ob das Entladen entsprechend vom Counter limitiert wird

    # setup
    bidi_cps("cp3")
    control_parameter = data.data.cp_data["cp3"].data.control_parameter
    control_parameter.chargemode = Chargemode.INSTANT_CHARGING
    data.data.cp_data["cp3"].data.get.max_discharge_power = -22000
    data.data.cp_data["cp3"].data.set.charging_ev_data.data.get.soc = 80
    data.data.cp_data["cp3"].data.set.charging_ev_data.charge_template.data.chargemode.instant_charging.dc_current = -20
    for counter in ("counter0", "counter6"):
        data.data.counter_data[counter].data.set.raw_exported_currents_left = [10]*3
    mock_get_component_name_by_id = Mock(return_value="Garage")
    monkeypatch.setattr(loadmanagement, "get_component_name_by_id", mock_get_component_name_by_id)

    # execution
    Algorithm().calc_current()

    # evaluation
    assert data.data.cp_data["cp3"].data.set.current == -10
    assert data.data.cp_data["cp4"].data.set.current == 0
    assert data.data.cp_data["cp5"].data.set.current == 0


@pytest.mark.parametrize(
    "max_discharge_power, expected_cp4_current, expected_cp5_current",
    [
        # Begrenzt durch max_discharge_power und Counter
        pytest.param(-11000, -15.942028985507246, -4.057971014492754, id="max_discharge_11kW"),
        # Nur durch Counter begrenzt
        pytest.param(-110000, -20, 0, id="max_discharge_110kW"),
    ],
)
def test_cp3_cp4_bidi_instant_discharge_splits_limited_export_current(
        max_discharge_power, expected_cp4_current, expected_cp5_current,
        bidi_cps, all_cp_not_charging, monkeypatch):
    # Beide CPs sind auf einer Ebene und wollen -20 A entladen
    # Counter erlaubt insgesamt nur -20 A pro Phase

    # setup
    bidi_cps("cp4", "cp5")
    for cp in ("cp4", "cp5"):
        control_parameter = data.data.cp_data[cp].data.control_parameter
        control_parameter.chargemode = Chargemode.INSTANT_CHARGING
        data.data.cp_data[cp].data.get.max_discharge_power = max_discharge_power
        data.data.cp_data[cp].data.set.charging_ev_data.data.get.soc = 80
        (data.data.cp_data[cp].data.set.charging_ev_data.charge_template.data
            .chargemode.instant_charging.dc_current) = -20

    for counter in ("counter0", "counter6"):
        data.data.counter_data[counter].data.set.raw_exported_currents_left = [20]*3
    mock_get_component_name_by_id = Mock(return_value="Garage")
    monkeypatch.setattr(loadmanagement, "get_component_name_by_id", mock_get_component_name_by_id)

    # execution
    Algorithm().calc_current()

    # evaluation
    assert data.data.cp_data["cp3"].data.set.current == 0
    assert data.data.cp_data["cp4"].data.set.current == expected_cp4_current
    assert data.data.cp_data["cp5"].data.set.current == expected_cp5_current


def test_cp4_bidi_discharge_unlocks_cp5_instant_charging_in_next_cycle(
        bidi_cps, all_cp_not_charging, monkeypatch):
    # Zyklus 1: CP4 entlaedt, CP5 bleibt bei 20 A (Counter-Limit 20 A).
    # Zyklus 2: Entladung ist am Counter reflektiert, dadurch kann CP5 auf 40 A steigen.

    # setup
    bidi_cps("cp4")
    cp4_control_parameter = data.data.cp_data["cp4"].data.control_parameter
    cp4_control_parameter.chargemode = Chargemode.INSTANT_CHARGING
    data.data.cp_data["cp4"].data.get.max_discharge_power = -22000
    data.data.cp_data["cp4"].data.set.charging_ev_data.data.get.soc = 80
    data.data.cp_data["cp4"].data.set.charging_ev_data.charge_template.data.chargemode.instant_charging.dc_current = -20

    cp5 = data.data.cp_data["cp5"]
    cp5_control_parameter = cp5.data.control_parameter
    cp5_control_parameter.chargemode = Chargemode.INSTANT_CHARGING
    cp5_control_parameter.submode = Chargemode.INSTANT_CHARGING
    cp5_control_parameter.phases = 3
    cp5_control_parameter.required_currents = [50]*3
    cp5_control_parameter.required_current = 50
    cp5.data.get.max_charge_power = 110000
    cp5.data.get.charge_state = True
    cp5.data.get.currents = [20]*3
    cp5.data.set.charging_ev_data.ev_template.data.max_current_multi_phases = 50
    cp5.template.data.max_current_multi_phases = 50

    for counter in ("counter0", "counter6"):
        data.data.counter_data[counter].data.set.raw_currents_left = [20]*3
        data.data.counter_data[counter].data.set.raw_exported_currents_left = [20]*3
        data.data.counter_data[counter].data.set.raw_power_left = 100000
        data.data.counter_data[counter].data.set.raw_exported_power_left = 100000

    mock_get_component_name_by_id = Mock(return_value="Garage")
    monkeypatch.setattr(loadmanagement, "get_component_name_by_id", mock_get_component_name_by_id)

    # execution + evaluation cycle 1
    Algorithm().calc_current()
    assert data.data.cp_data["cp4"].data.set.current == -20
    assert data.data.cp_data["cp5"].data.set.current == 20

    # Entladung aus Zyklus 1 ist im naechsten Zyklus als zusaetzlicher Spielraum verfuegbar.
    for counter in ("counter0", "counter6"):
        data.data.counter_data[counter].data.set.raw_currents_left = [40]*3

    # execution + evaluation cycle 2
    Algorithm().calc_current()
    assert data.data.cp_data["cp4"].data.set.current == -20
    assert data.data.cp_data["cp5"].data.set.current == 40
