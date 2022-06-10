from helpermodules import measurement_log


def test_get_totals():
    # execution
    totals = measurement_log._get_totals(SAMPLE)

    # evaluation
    assert totals == TOTALS


SAMPLE = [{'bat': {'all': {'exported': 0, 'imported': 58.774, 'soc': 51},
          'bat2': {'exported': 0, 'imported': 61.752, 'soc': 51}},
           'counter': {'counter0': {'exported': 3.816, 'imported': 0.284}},
           'cp': {'all': {'exported': 0, 'imported': 15},
                  'cp3': {'exported': 0, 'imported': 10},
                  'cp4': {'exported': 0, 'imported': 5},
                  'cp5': {'exported': 0, 'imported': 0}},
           'date': '13:41',
           'ev': {'ev0': {'soc': 0}},
           'pv': {'all': {'imported': 88}, 'pv1': {'imported': 92}},
           'timestamp': 1654861269},
          {'bat': {'all': {'exported': 0, 'imported': 146.108, 'soc': 53},
                   'bat2': {'exported': 0, 'imported': 149.099, 'soc': 53}},
           'counter': {'counter0': {'exported': 4.317, 'imported': 0.772}},
           'cp': {'all': {'exported': 0, 'imported': 100},
                  'cp3': {'exported': 0, 'imported': 20},
                  'cp4': {'exported': 0, 'imported': 80},
                  'cp5': {'exported': 0, 'imported': 0}},
           'date': '13:46',
           'ev': {'ev0': {'soc': 4}},
           'pv': {'all': {'imported': 214}, 'pv1': {'imported': 214}},
           'timestamp': 1654861569},
          {'bat': {'all': {'exported': 0, 'imported': 234.308, 'soc': 55},
                   'bat2': {'exported': 0, 'imported': 234.308, 'soc': 55}},
           'counter': {'counter0': {'exported': 4.921, 'imported': 1.384}},
           'cp': {'all': {'exported': 0, 'imported': 120},
                  # remove existing module
                  'cp4': {'exported': 0, 'imported': 90},
                  'cp5': {'exported': 0, 'imported': 0},
                  # add new module later
                  'cp6': {'exported': 0, 'imported': 64}},
           'date': '13:51',
           'ev': {'ev0': {'soc': 6}},
           'pv': {'all': {'imported': 339}, 'pv1': {'imported': 339}},
           'timestamp': 1654861869}]

TOTALS = {'bat': {'all': {'exported': 0, 'imported': 175.534, 'soc': 4},
          'bat2': {'exported': 0, 'imported': 172.556, 'soc': 4}},
          'counter': {'counter0': {'exported': 1.105, 'imported': 1.1}},
          'cp': {'all': {'exported': 0, 'imported': 105},
                 'cp3': {'exported': 0, 'imported': 10},
                 'cp4': {'exported': 0, 'imported': 85},
                 'cp5': {'exported': 0, 'imported': 0},
                 'cp6': {'exported': 0, 'imported': 64}},
          'ev': {'ev0': {'soc': 6}},
          'pv': {'all': {'imported': 251}, 'pv1': {'imported': 247}}}
