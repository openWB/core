from copy import deepcopy
from typing import Dict
import pytest

from helpermodules.measurement_logging.process_log_calculation import (
    analyse_percentage,
    _calculate_average_power,
    process_entry,
    calc_energy_imported_by_source,
    CalculationType)


@pytest.mark.parametrize("name",
                         ["regular",
                          "negative consumption",
                          "cp export"])
def test_analyse_percentage(name: str,
                            daily_log_entry_percentage: Dict,
                            daily_log_entry_percentage_negative_consumption: Dict,
                            daily_log_entry_percentage_cp_discharge: Dict):
    # setup
    if name == "regular":
        data = daily_log_entry_percentage
        expected = deepcopy(data)
        expected.update({"energy_source": {'bat': 0.2398, 'cp': 0.0, 'grid': 0.6504, 'pv': 0.1099}})
    elif name == "negative consumption":
        data = daily_log_entry_percentage_negative_consumption
        expected = deepcopy(data)
        expected.update({"energy_source": {'bat': 0.0, 'cp': 0.0, 'grid': 0.0, 'pv': 0.0}})
    elif name == "cp export":
        data = daily_log_entry_percentage_cp_discharge
        expected = deepcopy(data)
        expected.update({"energy_source": {'bat': 0.2006, 'cp': 0.1459, 'grid': 0.5441, 'pv': 0.1094}})

    # execution
    entry, message = analyse_percentage(data)

    # evaluation
    assert entry == expected
    assert message == ""


@pytest.mark.parametrize("test_case, entry_data, expected_energy_source, should_be_unchanged", [
    (
        "zero_consumption",
        {
            "timestamp": 1234567890,
            "date": "00:31",
            "bat": {"all": {"energy_imported": 5.0, "energy_exported": 5.0, "fault_state": 0}},
            "cp": {"all": {"energy_exported": 0.0, "fault_state": 0}},
            "pv": {"all": {"energy_exported": 0.0, "fault_state": 0}},
            "counter": {"counter0": {"grid": True, "energy_imported": 5.0, "energy_exported": 5.0, "fault_state": 0}}
        },
        {"grid": 0, "pv": 0, "bat": 0, "cp": 0},
        False
    ),
    (
        "missing_sections",
        {
            "timestamp": 1234567890,
            "date": "00:31",
            "counter": {"counter0": {"grid": True, "energy_imported": 10.0, "energy_exported": 2.0, "fault_state": 0}}
        },
        {"grid": 1.0, "pv": 0.0, "bat": 0.0, "cp": 0.0},
        False
    ),
    (
        "no_grid_counter",
        {
            "timestamp": 1234567890,
            "date": "00:31",
            "bat": {"all": {"energy_imported": 0.0, "energy_exported": 5.0, "fault_state": 0}},
            "counter": {"counter0": {"grid": False, "energy_imported": 10.0, "energy_exported": 2.0, "fault_state": 0}}
        },
        None,
        True
    )
])
def test_analyse_percentage_edge_cases(test_case, entry_data, expected_energy_source, should_be_unchanged):
    # execution
    result, message = analyse_percentage(entry_data)

    # evaluation
    if should_be_unchanged:
        # Entry should be unchanged, no energy_source added due to error
        assert result["timestamp"] == entry_data["timestamp"]
        assert "energy_source" not in result or result.get("energy_source") is None
    else:
        # Energy source should be calculated correctly
        assert result["energy_source"] == expected_energy_source
        assert message == ""


def test_calculate_average_power():
    # setup and execution
    power = _calculate_average_power(100, 250, 300)

    # evaluation
    assert power == 1800


def test_calc_energy_imported_by_source():
    # setup
    entry = {
        "timestamp": 1234567890,
        "energy_source": {"grid": 0.6523, "pv": 0.2487, "bat": 0.0789, "cp": 0.0201},
        "hc": {"all": {"energy_imported": 2345.6, "fault_state": 0}},
        "cp": {
            "cp1": {"energy_imported": 15723.4, "fault_state": 0},
            "cp2": {"energy_imported": 22108.7, "fault_state": 0}
        },
        "counter": {
            "counter0": {"grid": True, "energy_imported": 45892.3, "fault_state": 0},
            "counter1": {"grid": False, "energy_imported": 8956.7, "fault_state": 0}
        }
    }

    # execution
    result, message = calc_energy_imported_by_source(entry, {})

    # evaluation - realistic Wh values with decimal precision
    assert result["hc"]["all"]["energy_imported_grid"] == 1530.035
    assert result["hc"]["all"]["energy_imported_pv"] == 583.351
    assert result["hc"]["all"]["energy_imported_bat"] == 185.068
    assert result["hc"]["all"]["energy_imported_cp"] == 47.147

    assert result["cp"]["cp1"]["energy_imported_grid"] == 10256.374
    assert result["cp"]["cp1"]["energy_imported_pv"] == 3910.41
    assert result["cp"]["cp1"]["energy_imported_bat"] == 1240.576
    assert result["cp"]["cp1"]["energy_imported_cp"] == 316.04

    assert result["cp"]["cp2"]["energy_imported_grid"] == 14421.505
    assert result["cp"]["cp2"]["energy_imported_pv"] == 5498.434
    assert result["cp"]["cp2"]["energy_imported_bat"] == 1744.376
    assert result["cp"]["cp2"]["energy_imported_cp"] == 444.385

    assert result["counter"]["counter1"]["energy_imported_grid"] == 5842.455
    assert result["counter"]["counter1"]["energy_imported_pv"] == 2227.531
    assert result["counter"]["counter1"]["energy_imported_bat"] == 706.684
    assert result["counter"]["counter1"]["energy_imported_cp"] == 180.03
    # counter0 should not have these fields as it's a grid counter
    assert "energy_imported_grid" not in result["counter"]["counter0"]
    assert "energy_imported_pv" not in result["counter"]["counter0"]
    assert "energy_imported_bat" not in result["counter"]["counter0"]
    assert "energy_imported_cp" not in result["counter"]["counter0"]
    assert message == ""


def test_calc_energy_imported_by_source_message_filtering():
    """Test message filtering when component is in fault state and name is missing."""
    # setup
    entry = {
        "timestamp": 1234567890,
        "energy_source": {"grid": 0.6523, "pv": 0.2487, "bat": 0.0789, "cp": 0.0201},
        "cp": {
            "cp1": {"energy_imported": 15723.4, "fault_state": 0},
            "cp2": {"energy_imported": 22108.7, "fault_state": 2}  # fault state
        },
        "counter": {
            "counter0": {"grid": True, "energy_imported": 45892.3, "fault_state": 0},
            "counter1": {"grid": False, "energy_imported": 8956.7, "fault_state": 2}  # fault state
        }
    }

    # Names dict is missing keys for cp2 and counter1
    names = {
        "cp1": "Ladepunkt 1",
        "counter0": "EVU-Zähler"
        # cp2 and counter1 intentionally missing
    }

    # execution - filter messages only for cp2
    result, message = calc_energy_imported_by_source(entry, names, message_key_filter="cp2")

    # evaluation
    # Should only get message for cp2, not counter1 (due to filtering)
    expected_message = ("Die Anteile der Energiequellen für Ladepunkt cp2 konnten nicht berechnet werden, da er sich "
                        "im Fehlerzustand befindet. Die Verbräuche werden mit 0 kWh angesetzt.\n")
    assert message == expected_message

    # cp2 should have zero values for all energy sources due to fault state
    assert result["cp"]["cp2"]["energy_imported_grid"] == 0
    assert result["cp"]["cp2"]["energy_imported_pv"] == 0
    assert result["cp"]["cp2"]["energy_imported_bat"] == 0
    assert result["cp"]["cp2"]["energy_imported_cp"] == 0

    # cp1 should have normal calculated values (not in fault state)
    assert result["cp"]["cp1"]["energy_imported_grid"] == 10256.374

    # counter1 should have zero values but no message (filtered out)
    assert result["counter"]["counter1"]["energy_imported_grid"] == 0
    assert result["counter"]["counter1"]["energy_imported_pv"] == 0
    assert result["counter"]["counter1"]["energy_imported_bat"] == 0
    assert result["counter"]["counter1"]["energy_imported_cp"] == 0


def test_convert(daily_log_entry_processed, daily_log_sample):
    # setup and execution
    entry = process_entry(daily_log_sample[0], daily_log_sample[1], CalculationType.ALL)

    # evaluation
    assert entry == daily_log_entry_processed


def test_pv_export_and_bat_export_and_bat_import():
    entry = {
        "timestamp": 1234567890,
        "date": "00:00",
        "bat": {
            "all": {
                "energy_imported": 1.0,
                "energy_exported": 5.0,
                "fault_state": 0,
            }
        },
        "cp": {
            "all": {
                "energy_imported": 0.0,
                "energy_exported": 0.0,
                "fault_state": 0,
            }
        },
        "pv": {
            "all": {
                "energy_exported": 10.0,
                "fault_state": 0,
            }
        },
        "counter": {
            "counter0": {
                "grid": True,
                "energy_imported": 2.0,
                "energy_exported": 3.0,
                "fault_state": 0,
            }
        }
    }

    # Einspeisung - Priorität
    # 1 Pv
    # 2 Bat
    # 3 CP
    # -> erst komplette Einspeisung von PV berücksichtigen
    # -> wenn dann noch weitere Einspeisung übrig ist -> Bat und dann CP

    # Speicherimport - Priorität
    # 1 Pv
    # 2 Grid
    # 3 CP

    # Pv 10 Exported
    # Grid 2 Imported, 3 Exported
    # Bat   1 Imported, 5 Exported

    # Realer Verbrauch
    # 2 - 3 + 10 + 5 - 1 + 0 = 13

    # Export aufteilen
    # Pv - Export = 10 - 3 = 7

    # Bat import aufteilen
    # Pv - Bat_imported = 7 - 1 = 6

    # Tatsächlicher Verbrauch:
    # Pv = 6
    # Grid = 2
    # Bat = 5
    # ---------------------
    # Summe = 13

    # Anteil der Energiequellen:
    # Grid: 2/13 ≈ 0.1538
    # PV = 6/13 ≈ 0.4615
    # Bat = 5/13 ≈ 0.3846
    # CP = 0/13 ≈ 0.0
    result, message = analyse_percentage(entry)

    assert result["energy_source"] == {
        "grid": 0.1538,
        "pv": 0.4615,
        "bat": 0.3846,
        "cp": 0.0
    }
    assert message == ""


@pytest.mark.parametrize(
    "name, pv_exported, bat_exported, bat_imported, cp_exported, grid_imported, grid_exported, expected",
    [
        (
            "grid import and export",
            10.0,  # pv_exported
            0.0,  # bat_exported
            0.0,  # bat_imported
            0.0,  # cp_exported
            2.0,  # grid_imported
            3.0,  # grid_exported
            #        2/9           7/9
            {"grid": 0.2222, "pv": 0.7778, "bat": 0.0, "cp": 0.0}
        ),
        (
            "grid export proportional pv and bat",
            10.0,  # pv_exported
            5.0,  # bat_exported
            0.0,  # bat_imported
            0.0,  # cp_exported
            0.0,  # grid_imported
            3.0,  # grid_exported
            #        0/12        7/12           5/12
            {"grid": 0.0, "pv": 0.5833, "bat": 0.4167, "cp": 0.0}
        ),
        (
            "grid export and bat import",
            10.0,  # pv_exported
            5.0,  # bat_exported
            1.0,  # bat_imported
            0.0,  # cp_exported
            2.0,  # grid_imported
            3.0,  # grid_exported
            #        2/13        6/13           5/13
            {"grid": 0.1538, "pv": 0.4615, "bat": 0.3846, "cp": 0.0}
        ),
        (
            "grid export proportional pv and cp ",
            6.0,  # pv_exported
            0.0,  # bat_exported
            0.0,  # bat_imported
            3.0,  # cp_exported
            0.0,  # grid_imported
            3.0,  # grid_exported
            #        0/6        3/6           0/6       3/6
            {"grid": 0.0, "pv": 0.5, "bat": 0.0, "cp": 0.5}
        ),
        (
            "bat import proportional pv and grid",
            8.0,  # pv_exported
            0.0,  # bat_exported
            2.0,  # bat_imported
            0.0,  # cp_exported
            2.0,  # grid_imported
            0.0,  # grid_exported
            #        2/8        6/8           0/8       8/8
            {"grid": 0.25, "pv": 0.75, "bat": 0.0, "cp": 0.0}
        ),
    ]
)
def test_analyse_percentage_proportional_distribution(name,
                                                      pv_exported,
                                                      bat_exported,
                                                      bat_imported,
                                                      cp_exported,
                                                      grid_imported,
                                                      grid_exported, expected):
    entry = {
        "timestamp": 1234567890,
        "date": "00:00",
        "bat": {
            "all": {
                "energy_imported": bat_imported,
                "energy_exported": bat_exported,
                "fault_state": 0,
            }
        },
        "cp": {
            "all": {
                "energy_exported": cp_exported,
                "fault_state": 0,
            }
        },
        "pv": {
            "all": {
                "energy_exported": pv_exported,
                "fault_state": 0,
            }
        },
        "counter": {
            "counter0": {
                "grid": True,
                "energy_imported": grid_imported,
                "energy_exported": grid_exported,
                "fault_state": 0,
            }
        }
    }

    result, message = analyse_percentage(entry)

    assert result["energy_source"] == expected
    assert message == ""

    # Strommix muss zusammen 100% ergeben
    assert sum(result["energy_source"].values()) == pytest.approx(1.0, abs=0.0002)
