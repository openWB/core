from copy import deepcopy
from unittest.mock import Mock
from helpermodules.measurement_logging import process_log
from helpermodules.measurement_logging.process_log import (
    analyse_percentage,
    _calculate_average_power,
    process_entry,
    get_totals,
    CalculationType)


def test_get_totals(daily_log_sample, daily_log_totals):
    # setup and execution
    entries = deepcopy(daily_log_sample)
    totals = get_totals(entries)

    # evaluation
    assert totals == daily_log_totals


def test_analyse_percentage(daily_log_entry_kw_percentage):
    # setup
    expected = deepcopy(daily_log_entry_kw_percentage)
    expected.update({"energy_source":  {'bat': 0.2398, 'cp': 0.0, 'grid': 0.6504, 'pv': 0.1098}})
    expected["cp"]["all"].update({
        "energy_imported_bat": 0.23,
        "energy_imported_cp": 0.0,
        "energy_imported_grid": 0.624,
        "energy_imported_pv": 0.105})
    expected["hc"]["all"].update({
        "energy_imported_bat": 0.002,
        "energy_imported_cp": 0.0,
        "energy_imported_grid": 0.007,
        "energy_imported_pv": 0.001})

    # execution
    entry = analyse_percentage(daily_log_entry_kw_percentage)

    # evaluation
    assert entry == expected


def test_convert_value_to_kW():
    # setup and execution
    power = _calculate_average_power(100, 250, 300)

    # evaluation
    assert power == 1800


def test_convert(daily_log_entry_kw, daily_log_sample):
    # setup and execution
    entry = process_entry(daily_log_sample[0], daily_log_sample[1], CalculationType.ALL)

    # evaluation
    assert entry == daily_log_entry_kw


def test_get_daily_log(monkeypatch):
    # setup
    # packages_folder = Path(__file__).resolve().parents[3]/"packages"
    # with open(f"{packages_folder}/helpermodules/measurement_logging/20250616.json", "r") as file:
    #     daily_log = json.loads(file.read())
    collect_daily_log_data_mock = Mock(return_value=counter_jumps_forward)
    monkeypatch.setattr(process_log, "_collect_daily_log_data", collect_daily_log_data_mock)

    # execution
    daily_log_processed = process_log.get_daily_log("20250616")

    # evaluation
    assert daily_log_processed == counter_jumps_forward_processed


# Wenn ein Zwischenzähler nicht auslesbar war, soll beim Sprung der Anteil auf das Netz gerechnet werden.
counter_jumps_forward = {'entries': [{'bat': {'all': {'exported': 3195.13,
                                                      'imported': 629.37,
                                                      'soc': 48},
                                              'bat2': {'exported': 3195.13,
                                                       'imported': 629.37,
                                                       'soc': 48}},
                                      'counter': {'counter0': {'exported': 26029.945,
                                                               'grid': True,
                                                               'imported': 2728.572},
                                                  'counter2': {'exported': 26029.945,
                                                               'grid': False,
                                                               'imported': 0}},
                                      'cp': {'all': {'exported': 0, 'imported': 12639.11},
                                             'cp3': {'exported': 0, 'imported': 12639.11},
                                             'cp4': {'exported': 0, 'imported': 0},
                                             'cp5': {'exported': 0, 'imported': 0}},
                                      'date': '14:25',
                                      'ev': {'ev0': {'soc': None}},
                                      'hc': {'all': {'imported': 2324.001611140539}},
                                      'prices': {'bat': 0.0002, 'grid': 0.0003, 'pv': 0.00015},
                                      'pv': {'all': {'exported': 35827}, 'pv1': {'exported': 35827}},
                                      'sh': {},
                                      'timestamp': 1750767902},
                                     {'bat': {'all': {'exported': 3195.13,
                                                      'imported': 629.37,
                                                      'soc': 48},
                                              'bat2': {'exported': 3195.13,
                                                       'imported': 629.37,
                                                       'soc': 48}},
                                      'counter': {'counter0': {'exported': 26802.355,
                                                               'grid': True,
                                                               'imported': 2728.572},
                                                  'counter2': {'exported': 26029.945,
                                                               'grid': True,
                                                               'imported': 2728.572}},
                                      'cp': {'all': {'exported': 0, 'imported': 12639.11},
                                             'cp3': {'exported': 0, 'imported': 12639.11},
                                             'cp4': {'exported': 0, 'imported': 0},
                                             'cp5': {'exported': 0, 'imported': 0}},
                                      'date': '14:30',
                                      'ev': {'ev0': {'soc': None}},
                                      'hc': {'all': {'imported': 2361.178611303703}},
                                      'prices': {'bat': 0.0002, 'grid': 0.0003, 'pv': 0.00015},
                                      'pv': {'all': {'exported': 36636}, 'pv1': {'exported': 36636}},
                                      'sh': {},
                                      'timestamp': 1750768201}],
                         'names': {'bat2': 'MQTT-Speicher',
                                   'counter0': 'MQTT-Zähler',
                                   'counter2': 'Test-Zähler',
                                   'cp3': 'MQTT-Ladepunkt',
                                   'cp4': 'MQTT-Ladepunkt',
                                   'cp5': 'MQTT-Ladepunkt',
                                   'ev0': 'Standard-Fahrzeug',
                                   'pv1': 'MQTT-Wechselrichter'}}

counter_jumps_forward_processed = {'entries': [{'bat': {'all': {'energy_exported': 0.0,
                                                                'energy_imported': 0.0,
                                                                'exported': 3195.13,
                                                                'imported': 629.37,
                                                                'power_average': 0.0,
                                                                'power_exported': 0,
                                                                'power_imported': 0.0,
                                                                'soc': 48},
                                                        'bat2': {'energy_exported': 0.0,
                                                                 'energy_imported': 0.0,
                                                                 'exported': 3195.13,
                                                                 'imported': 629.37,
                                                                 'power_average': 0.0,
                                                                 'power_exported': 0,
                                                                 'power_imported': 0.0,
                                                                 'soc': 48}},
                                                'counter': {'counter0': {'energy_exported': 0.772,
                                                                         'energy_imported': 0.0,
                                                                         'exported': 26029.945,
                                                                         'grid': True,
                                                                         'imported': 2728.572,
                                                                         'power_average': -9.3,
                                                                         'power_exported': 9.3,
                                                                         'power_imported': 0},
                                                            'counter2': {'energy_exported': 0.0,
                                                                         'energy_imported': 2.729,
                                                                         'energy_imported_bat': 0.0,
                                                                         'energy_imported_cp': 0.0,
                                                                         'energy_imported_grid': 2.729,
                                                                         'energy_imported_pv': 0.0,
                                                                         'exported': 26029.945,
                                                                         'grid': False,
                                                                         'imported': 0,
                                                                         'power_average': 32.852,
                                                                         'power_exported': 0,
                                                                         'power_imported': 32.852}},
                                                'cp': {'all': {'energy_exported': 0.0,
                                                               'energy_imported': 0.0,
                                                               'energy_imported_bat': 0.0,
                                                               'energy_imported_cp': 0.0,
                                                               'energy_imported_grid': 0.0,
                                                               'energy_imported_pv': 0.0,
                                                               'exported': 0,
                                                               'imported': 12639.11,
                                                               'power_average': 0.0,
                                                               'power_exported': 0,
                                                               'power_imported': 0.0},
                                                       'cp3': {'energy_exported': 0.0,
                                                               'energy_imported': 0.0,
                                                               'energy_imported_bat': 0.0,
                                                               'energy_imported_cp': 0.0,
                                                               'energy_imported_grid': 0.0,
                                                               'energy_imported_pv': 0.0,
                                                               'exported': 0,
                                                               'imported': 12639.11,
                                                               'power_average': 0.0,
                                                               'power_exported': 0,
                                                               'power_imported': 0.0},
                                                       'cp4': {'energy_exported': 0.0,
                                                               'energy_imported': 0.0,
                                                               'energy_imported_bat': 0.0,
                                                               'energy_imported_cp': 0.0,
                                                               'energy_imported_grid': 0.0,
                                                               'energy_imported_pv': 0.0,
                                                               'exported': 0,
                                                               'imported': 0,
                                                               'power_average': 0.0,
                                                               'power_exported': 0,
                                                               'power_imported': 0.0},
                                                       'cp5': {'energy_exported': 0.0,
                                                               'energy_imported': 0.0,
                                                               'energy_imported_bat': 0.0,
                                                               'energy_imported_cp': 0.0,
                                                               'energy_imported_grid': 0.0,
                                                               'energy_imported_pv': 0.0,
                                                               'exported': 0,
                                                               'imported': 0,
                                                               'power_average': 0.0,
                                                               'power_exported': 0,
                                                               'power_imported': 0.0}},
                                                'date': '14:25',
                                                'energy_source': {'bat': 0.0, 'cp': 0.0, 'grid': 1.0, 'pv': 0.0},
                                                'ev': {'ev0': {'soc': None}},
                                                'hc': {'all': {'energy_exported': 0.0,
                                                               'energy_imported': 0.037,
                                                               'energy_imported_bat': 0.0,
                                                               'energy_imported_cp': 0.0,
                                                               'energy_imported_grid': 0.037,
                                                               'energy_imported_pv': 0.0,
                                                               'imported': 2324.001611140539,
                                                               'power_average': 0.448,
                                                               'power_exported': 0,
                                                               'power_imported': 0.448}},
                                                'prices': {'bat': 0.0002, 'grid': 0.0003, 'pv': 0.00015},
                                                'pv': {'all': {'energy_exported': 0.809,
                                                               'energy_imported': 0.0,
                                                               'exported': 35827,
                                                               'power_average': -9.74,
                                                               'power_exported': 9.74,
                                                               'power_imported': 0},
                                                       'pv1': {'energy_exported': 0.809,
                                                               'energy_imported': 0.0,
                                                               'exported': 35827,
                                                               'power_average': -9.74,
                                                               'power_exported': 9.74,
                                                               'power_imported': 0}},
                                                'sh': {},
                                                'timestamp': 1750767902}],
                                   'names': {'bat2': 'MQTT-Speicher',
                                             'counter0': 'MQTT-Zähler',
                                             'counter2': 'Test-Zähler',
                                             'cp3': 'MQTT-Ladepunkt',
                                             'cp4': 'MQTT-Ladepunkt',
                                             'cp5': 'MQTT-Ladepunkt',
                                             'ev0': 'Standard-Fahrzeug',
                                             'pv1': 'MQTT-Wechselrichter'},
                                   'totals': {'bat': {'all': {'energy_exported': 0.0, 'energy_imported': 0.0},
                                                      'bat2': {'energy_exported': 0.0, 'energy_imported': 0.0}},
                                              'counter': {'counter0': {'energy_exported': 772.0,
                                                                       'energy_imported': 0.0,
                                                                       'grid': True},
                                                          'counter2': {'energy_exported': 0.0,
                                                                       'energy_imported': 2729.0,
                                                                       'energy_imported_bat': 0.0,
                                                                       'energy_imported_cp': 0.0,
                                                                       'energy_imported_grid': 2729.0,
                                                                       'energy_imported_pv': 0.0,
                                                                       'grid': False}},
                                              'cp': {'all': {'energy_exported': 0.0,
                                                             'energy_imported': 0.0,
                                                             'energy_imported_bat': 0.0,
                                                             'energy_imported_cp': 0.0,
                                                             'energy_imported_grid': 0.0,
                                                             'energy_imported_pv': 0.0},
                                                     'cp3': {'energy_exported': 0.0,
                                                             'energy_imported': 0.0,
                                                             'energy_imported_bat': 0.0,
                                                             'energy_imported_cp': 0.0,
                                                             'energy_imported_grid': 0.0,
                                                             'energy_imported_pv': 0.0},
                                                     'cp4': {'energy_exported': 0.0,
                                                             'energy_imported': 0.0,
                                                             'energy_imported_bat': 0.0,
                                                             'energy_imported_cp': 0.0,
                                                             'energy_imported_grid': 0.0,
                                                             'energy_imported_pv': 0.0},
                                                     'cp5': {'energy_exported': 0.0,
                                                             'energy_imported': 0.0,
                                                             'energy_imported_bat': 0.0,
                                                             'energy_imported_cp': 0.0,
                                                             'energy_imported_grid': 0.0,
                                                             'energy_imported_pv': 0.0}},
                                              'hc': {'all': {'energy_imported': 37.0,
                                                             'energy_imported_bat': 0.0,
                                                             'energy_imported_cp': 0.0,
                                                             'energy_imported_grid': 37.0,
                                                             'energy_imported_pv': 0.0}},
                                              'pv': {'all': {'energy_exported': 809.0},
                                                     'pv1': {'energy_exported': 809.0}},
                                              'sh': {}}}
