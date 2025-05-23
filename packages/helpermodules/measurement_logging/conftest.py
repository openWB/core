from threading import Event
import pytest

from control.chargepoint import chargepoint
from control.chargepoint.chargepoint_all import AllChargepoints
from control import bat_all, counter, pv_all, pv
from control import data


@pytest.fixture(autouse=True)
def data_module() -> None:
    data.data_init(Event())
    data.data.bat_data.update({"all": bat_all.BatAll(), "bat2": bat_all.Bat(2)})
    data.data.counter_data.update({"counter0": counter.Counter(0)})
    data.data.cp_all_data = AllChargepoints()
    data.data.cp_data.update({"cp4": chargepoint.Chargepoint(
        4, None), "cp5": chargepoint.Chargepoint(5, None), "cp6": chargepoint.Chargepoint(6, None)})
    data.data.pv_data.update({"all": pv_all.PvAll(), "pv1": pv.Pv(1)})


@pytest.fixture()
def daily_log_sample():
    return [{"timestamp": 1690529761,
             "date": "09:35",
             "cp": {
                 "cp3": {"imported": 3620.971, "exported": 0},
                 "cp5": {"imported": 1208.646, "exported": 0},
                 "cp4": {"imported": 1198.566, "exported": 0},
                 "all": {"imported": 6028.183, "exported": 0}},
             "ev": {"ev0": {"soc": 0}},
             "counter": {"counter0": {"imported": 4686.054, "exported": 2.396, "grid": True}},
             "pv": {"pv1": {"exported": 804}, "all": {"exported": 804}},
             "bat": {"bat2": {"imported": 2.42, "exported": 1742.135, "soc": 15},
                     "all": {"imported": 2.42, "exported": 1742.135, "soc": 15}},
             "sh": {"sh1": {"temp0": 300, "temp1": 300, "temp2": 300, "imported": 0.1, "exported": 0}},
             "hc": {"all": {"imported": 100}}},
            {"timestamp": 1690530060,
             "date": "09:40",
             "cp": {
                 "cp3": {"imported": 4196.737, "exported": 0},
                 "cp5": {"imported": 1400.574, "exported": 0},
                 "cp4": {"imported": 1390.685, "exported": 0},
                 "all": {"imported": 6987.995999999999, "exported": 0}},
             "ev": {"ev0": {"soc": 0}},
             "counter": {"counter0": {"imported": 5432.177, "exported": 2.396, "grid": True}},
             "pv": {"pv1": {"exported": 930}, "all": {"exported": 930}},
             "bat": {"bat2": {"imported": 2.42, "exported": 2017.569, "soc": 10},
                     "all": {"imported": 2.42, "exported": 2017.569, "soc": 10}},
             "sh": {"sh1": {"temp0": 300, "temp1": 300, "temp2": 300, "imported": 0.2, "exported": 0}},
             "hc": {"all": {"imported": 110}}},
            {"timestamp": 1690530360,
             "date": "09:45",
             "cp": {
                 "cp3": {"imported": 4772.491, "exported": 0},
                 "cp6": {"imported": 1592.81, "exported": 0},
                 "cp4": {"imported": 1582.508, "exported": 0},
                 "all": {"imported": 7947.808999999999, "exported": 0}},
             "ev": {"ev0": {"soc": 0}},
             "counter": {"counter0": {"imported": 6178.065, "exported": 2.396, "grid": True}},
             "pv": {"pv1": {"exported": 1055}, "all": {"exported": 1055}},
             "bat": {"bat2": {"imported": 2.42, "exported": 2292.992, "soc": 4},
                     "all": {"imported": 2.42, "exported": 2292.992, "soc": 4}},
             "sh": {"sh1": {"temp0": 300, "temp1": 300, "temp2": 300, "imported": 0.4, "exported": 0}},
             "hc": {"all": {"imported": 120}}}
            ]


@pytest.fixture()
def daily_log_totals():
    return {'bat': {'all': {'energy_exported': 550.0, 'energy_imported': 0.0},
                    'bat2': {'energy_exported': 550.0, 'energy_imported': 0.0}},
            'counter': {'counter0': {'energy_exported': 0.0, 'energy_imported': 1492.0, 'grid': True}},
            'cp': {'all': {'energy_exported': 0.0, 'energy_imported': 1920.0},
                   'cp3': {'energy_exported': 0.0, 'energy_imported': 1152.0},
                   'cp4': {'energy_exported': 0.0, 'energy_imported': 384.0},
                   'cp5': {'energy_exported': 0.0, 'energy_imported': 192.0},
                   'cp6': {'energy_exported': 0.0, 'energy_imported': 0}},
            'pv': {'all': {'energy_exported': 251.0}, 'pv1': {'energy_exported': 251.0}},
            "sh": {"sh1": {"energy_imported": 0.0, "energy_exported": 0.0}},
            "hc": {"all": {"energy_imported": 20.0}}}


@pytest.fixture()
def daily_log_entry_kw():
    return {"timestamp": 1690529761,
            "date": "09:35",
            "cp": {
                "cp3": {
                    "imported": 3620.971,
                    "exported": 0,
                    "power_average": 6.932,
                    "power_imported": 6.932,
                    "power_exported": 0.0,
                    "energy_imported": 0.576,
                    "energy_exported": 0.0
                },
                "cp5": {
                    "imported": 1208.646,
                    "exported": 0,
                    "power_average": 2.311,
                    "power_imported": 2.311,
                    "power_exported": 0.0,
                    "energy_imported": 0.192,
                    "energy_exported": 0.0
                },
                "cp4": {
                    "imported": 1198.566,
                    "exported": 0,
                    "power_average": 2.313,
                    "power_imported": 2.313,
                    "power_exported": 0.0,
                    "energy_imported": 0.192,
                    "energy_exported": 0.0
                },
                "all": {
                    "imported": 6028.183,
                    "exported": 0,
                    "power_average": 11.556,
                    "power_imported": 11.556,
                    "power_exported": 0.0,
                    "energy_imported": 0.96,
                    "energy_exported": 0.0
                }
            },            "ev": {
                "ev0": {
                    "soc": 0
                }
            },
            "counter": {
                "counter0": {
                    "imported": 4686.054,
                    "exported": 2.396,
                    "grid": True,
                    "power_average": 8.983,
                    "power_imported": 8.983,
                    "power_exported": 0.0,
                    "energy_imported": 0.746,
                    "energy_exported": 0.0
                }
            },
            "pv": {
                "pv1": {
                    "exported": 804,
                    "power_average": -1.517,
                    "power_imported": 0.0,
                    "power_exported": 1.517,
                    "energy_imported": 0.0,
                    "energy_exported": 0.126
                },
                "all": {
                    "exported": 804,
                    "power_average": -1.517,
                    "power_imported": 0.0,
                    "power_exported": 1.517,
                    "energy_imported": 0.0,
                    "energy_exported": 0.126
                }
            },
            "bat": {
                "bat2": {
                    "imported": 2.42,
                    "exported": 1742.135,
                    "soc": 15,
                    "power_average": -3.316,
                    "power_imported": 0.0,
                    "power_exported": 3.316,
                    "energy_imported": 0.0,
                    "energy_exported": 0.275
                },
                "all": {
                    "imported": 2.42,
                    "exported": 1742.135,
                    "soc": 15,
                    "power_average": -3.316,
                    "power_imported": 0.0,
                    "power_exported": 3.316,
                    "energy_imported": 0.0,
                    "energy_exported": 0.275
                }
            },
            "sh": {
                "sh1": {
                    "temp0": 300,
                    "temp1": 300,
                    "temp2": 300,
                    "imported": 0.1,
                    "exported": 0,
                    "power_average": 0.001,
                    "power_imported": 0.001,
                    "power_exported": 0.0,
                    "energy_imported": 0.0,
                    "energy_exported": 0.0
                }
            },
            'hc': {'all': {'energy_exported': 0.0,
                           'energy_imported': 0.01,
                           'imported': 100,
                           'power_average': 0.12,
                           'power_exported': 0.0,
                           'power_imported': 0.12}}}


@pytest.fixture()
def daily_log_entry_kw_percentage():
    return {
        'bat': {'all': {'energy_exported': 0.275,
                        'energy_imported': 0.0,
                        'exported': 1742.135,
                        'imported': 2.42,
                        'power_average': -3.316,
                        'power_exported': 3.316,
                        'power_imported': 0.0,
                        'soc': 15},
                'bat2': {'energy_exported': 0.275,
                         'energy_imported': 0.0,
                         'exported': 1742.135,
                         'imported': 2.42,
                         'power_average': -3.316,
                         'power_exported': 3.316,
                         'power_imported': 0.0,
                         'soc': 15}},
        'counter': {'counter0': {'energy_exported': 0.0,
                                 'energy_imported': 0.746,
                                 'exported': 2.396,
                                 'grid': True,
                                 'imported': 4686.054,
                                 'power_average': 8.983,
                                 'power_exported': 0.0,
                                 'power_imported': 8.983}},
        'cp': {'all': {'energy_exported': 0.0,
                       'energy_imported': 0.96,
                       'energy_imported_bat': 0.23,
                       'energy_imported_cp': 0.0,
                       'energy_imported_grid': 0.624,
                       'energy_imported_pv': 0.105,
                       'exported': 0,
                       'imported': 6028.183,
                       'power_average': 11.556,
                       'power_exported': 0.0,
                       'power_imported': 11.556},
               'cp3': {'energy_exported': 0.0,
                       'energy_imported': 0.576,
                       'energy_imported_bat': 0.138,
                       'energy_imported_cp': 0.0,
                       'energy_imported_grid': 0.375,
                       'energy_imported_pv': 0.063,
                       'exported': 0,
                       'imported': 3620.971,
                       'power_average': 6.932,
                       'power_exported': 0.0,
                       'power_imported': 6.932},
               'cp4': {'energy_exported': 0.0,
                       'energy_imported': 0.192,
                       'energy_imported_bat': 0.046,
                       'energy_imported_cp': 0.0,
                       'energy_imported_grid': 0.125,
                       'energy_imported_pv': 0.021,
                       'exported': 0,
                       'imported': 1198.566,
                       'power_average': 2.313,
                       'power_exported': 0.0,
                       'power_imported': 2.313},
               'cp5': {'energy_exported': 0.0,
                       'energy_imported': 0.192,
                       'energy_imported_bat': 0.046,
                       'energy_imported_cp': 0.0,
                       'energy_imported_grid': 0.125,
                       'energy_imported_pv': 0.021,
                       'exported': 0,
                       'imported': 1208.646,
                       'power_average': 2.311,
                       'power_exported': 0.0,
                       'power_imported': 2.311}},
        'date': '09:35',
        'energy_source': {'bat': 0.2398,
                          'cp': 0.0,
                          'grid': 0.6504,
                          'pv': 0.1098},
        'ev': {'ev0': {'soc': 0}},
        'hc': {'all': {'energy_exported': 0.0,
                       'energy_imported': 0.01,
                       'energy_imported_bat': 0.002,
                       'energy_imported_cp': 0.0,
                       'energy_imported_grid': 0.007,
                       'energy_imported_pv': 0.001,
                       'imported': 100,
                       'power_average': 0.12,
                       'power_exported': 0.0,
                       'power_imported': 0.12}},
        'pv': {'all': {'energy_exported': 0.126,
                       'energy_imported': 0.0,
                       'exported': 804,
                       'power_average': -1.517,
                       'power_exported': 1.517,
                       'power_imported': 0.0},
               'pv1': {'energy_exported': 0.126,
                       'energy_imported': 0.0,
                       'exported': 804,
                       'power_average': -1.517,
                       'power_exported': 1.517,
                       'power_imported': 0.0}},
        'sh': {'sh1': {'energy_exported': 0.0,
                       'energy_imported': 0.0,
                       'exported': 0,
                       'imported': 0.1,
                       'power_average': 0.001,
                       'power_exported': 0.0,
                       'power_imported': 0.001,
                       'temp0': 300,
                       'temp1': 300,
                       'temp2': 300}},
        'timestamp': 1690529761,
    }
