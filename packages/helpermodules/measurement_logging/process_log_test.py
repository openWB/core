from helpermodules.measurement_logging.process_log import (
    # _analyse_percentage,
    _calculate_average_power,
    _process_entry,
    get_totals,
    CalculationType)


def test_get_totals(daily_log_sample, daily_log_totals):
    # setup and execution
    totals = get_totals(daily_log_sample)

    # evaluation
    assert totals == daily_log_totals


# def test_analyse_percentage(daily_log_entry_kw):
#     # setup and execution
#     entry = _analyse_percentage(daily_log_entry_kw)

#     # evaluation
#     assert entry == {'bat': {'all': {'energy_exported': 3.316262207357859, 'energy_imported': 0.0, 'soc': 15},
#                              'bat2': {'energy_exported': 3.316262207357859, 'energy_imported': 0.0, 'soc': 15}},
#                      'counter': {'counter0': {'energy_exported': 0.0,
#                                               'grid': True,
#                                               'energy_imported': 8.983420735785948}},
#                      'cp': {'all': {'energy_exported': 0.0, 'energy_imported': 11.556276923076913},
#                             'cp3': {'energy_exported': 0.0, 'energy_imported': 6.932299665551841},
#                             'cp4': {'energy_exported': 0.0, 'energy_imported': 2.3131384615384603},
#                             'cp5': {'energy_exported': 0.0, 'energy_imported': 2.3108387959866237}},
#                      'date': '09:35',
#                      'ev': {'ev0': {'soc': 0}},
#                      'pv': {'all': {'energy_exported': 1.517056856187291},
#                             'pv1': {'energy_exported': 1.517056856187291}},
#                      'sh': {'sh1': {'energy_exported': 0.0,
#                                     'energy_imported': 0.0012040133779264216,
#                                     'temp0': 300,
#                                     'temp1': 300,
#                                     'temp2': 300}},
#                      'timestamp': 1690529761,
#                      "power_source": {"grid": 65.02, "pv": 10.98, "bat": 24.0, "cp": 0.0}}


def test_convert_value_to_kW():
    # setup and execution
    power = _calculate_average_power(100, 250, 300)

    # evaluation
    assert power == 1.8


def test_convert(daily_log_entry_kw, daily_log_sample):
    # setup and execution
    entry = _process_entry(daily_log_sample[0], daily_log_sample[1], CalculationType.ALL)

    # evaluation
    assert entry == daily_log_entry_kw
