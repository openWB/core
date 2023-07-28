from helpermodules.measurement_logging.process_log import (_analyse_percentage, _convert, _convert_value_to_kW,
                                                           get_totals)


def test_get_totals(daily_log_sample, daily_log_totals):
    # setup and execution
    totals = get_totals(daily_log_sample)

    # evaluation
    assert totals == daily_log_totals


def test_analyse_percentage(daily_log_entry_kw):
    # setup and execution
    entry = _analyse_percentage(daily_log_entry_kw)

    # evaluation
    assert entry == {'bat': {'all': {'exported': 3.316262207357859, 'imported': 0.0, 'soc': 15},
                             'bat2': {'exported': 3.316262207357859, 'imported': 0.0, 'soc': 15}},
                     'counter': {'counter0': {'exported': 0.0,
                                              'grid': True,
                                              'imported': 8.983420735785948}},
                     'cp': {'all': {'exported': 0.0, 'imported': 11.556276923076913},
                            'cp3': {'exported': 0.0, 'imported': 6.932299665551841},
                            'cp4': {'exported': 0.0, 'imported': 2.3131384615384603},
                            'cp5': {'exported': 0.0, 'imported': 2.3108387959866237}},
                     'date': '09:35',
                     'ev': {'ev0': {'soc': 0}},
                     'pv': {'all': {'exported': 1.517056856187291},
                            'pv1': {'exported': 1.517056856187291}},
                     'sh': {'sh1': {'exported': 0.0,
                                    'imported': 0.0012040133779264216,
                                    'temp0': 300,
                                    'temp1': 300,
                                    'temp2': 300}},
                     'timestamp': 1690529761,
                     "power_source": {"grid": 65.02, "pv": 10.98, "bat": 24.0, "cp": 0.0}}


def test_convert_value_to_kW():
    # setup and execution
    power = _convert_value_to_kW(100, 250, 300)

    # evaluation
    assert power == 1.8


def test_convert(daily_log_entry_kw, daily_log_sample):
    # setup and execution
    entry = _convert(daily_log_sample[0], daily_log_sample[1])

    # evaluation
    assert entry == daily_log_entry_kw
