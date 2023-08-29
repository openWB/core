import threading
import pytest
from control.chargepoint import chargepoint

from control.chargepoint.chargepoint_all import AllChargepoints
from control import bat_all, counter, pv_all, pv
from control import data


@pytest.fixture(autouse=True)
def data_module() -> None:
    data.data_init(threading.Event())
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
    return {'bat': {'all': {'exported': 550.857, 'imported': 0.0},
                    'bat2': {'exported': 550.857, 'imported': 0.0}},
            'counter': {'counter0': {'exported': 0.0, 'imported': 1492.011}},
            'cp': {'all': {'exported': 0, 'imported': 1919.625999999999},
                   'cp3': {'exported': 0, 'imported': 1151.52},
                   'cp4': {'exported': 0, 'imported': 383.942},
                   'cp5': {'exported': 0, 'imported': 191.928},
                   'cp6': {'exported': 0, 'imported': 0}},
            'pv': {'all': {'exported': 251}, 'pv1': {'exported': 251}},
            "sh": {"sh1": {"imported": 0.3, "exported": 0}},
            "hc": {"all": {"imported": 20}}}


@pytest.fixture()
def daily_log_entry_kw():
    return {"timestamp": 1690529761,
            "date": "09:35",
            "cp": {
                "cp3": {
                    "imported": 3620.971,
                    "exported": 0,
                    "power_average": 6.932299665551841,
                    "power_imported": 6.932299665551841,
                    "power_exported": 0,
                    "energy_imported": 0.5757660000000001,
                    "energy_exported": 0
                },
                "cp5": {
                    "imported": 1208.646,
                    "exported": 0,
                    "power_average": 2.3108387959866237,
                    "power_imported": 2.3108387959866237,
                    "power_exported": 0,
                    "energy_imported": 0.1919280000000001,
                    "energy_exported": 0
                },
                "cp4": {
                    "imported": 1198.566,
                    "exported": 0,
                    "power_average": 2.3131384615384603,
                    "power_imported": 2.3131384615384603,
                    "power_exported": 0,
                    "energy_imported": 0.1921189999999999,
                    "energy_exported": 0
                },
                "all": {
                    "imported": 6028.183,
                    "exported": 0,
                    "power_average": 11.556276923076913,
                    "power_imported": 11.556276923076913,
                    "power_exported": 0,
                    "energy_imported": 0.9598129999999991,
                    "energy_exported": 0
                }
            },
            "ev": {
                "ev0": {
                    "soc": 0
                }
            },
            "counter": {
                "counter0": {
                    "imported": 4686.054,
                    "exported": 2.396,
                    "grid": True,
                    "power_average": 8.983420735785948,
                    "power_imported": 8.983420735785948,
                    "power_exported": 0,
                    "energy_imported": 0.7461229999999996,
                    "energy_exported": 0
                }
            },
            "pv": {
                "pv1": {
                    "exported": 804,
                    "power_average": -1.517056856187291,
                    "power_imported": 0,
                    "power_exported": 1.517056856187291,
                    "energy_imported": 0,
                    "energy_exported": 0.126
                },
                "all": {
                    "exported": 804,
                    "power_average": -1.517056856187291,
                    "power_imported": 0,
                    "power_exported": 1.517056856187291,
                    "energy_imported": 0,
                    "energy_exported": 0.126
                }
            },
            "bat": {
                "bat2": {
                    "imported": 2.42,
                    "exported": 1742.135,
                    "soc": 15,
                    "power_average": -3.316262207357859,
                    "power_imported": 0,
                    "power_exported": 3.316262207357859,
                    "energy_imported": 0,
                    "energy_exported": 0.27543399999999996
                },
                "all": {
                    "imported": 2.42,
                    "exported": 1742.135,
                    "soc": 15,
                    "power_average": -3.316262207357859,
                    "power_imported": 0,
                    "power_exported": 3.316262207357859,
                    "energy_imported": 0,
                    "energy_exported": 0.27543399999999996
                }
            },
            "sh": {
                "sh1": {
                    "temp0": 300,
                    "temp1": 300,
                    "temp2": 300,
                    "imported": 0.1,
                    "exported": 0,
                    "power_average": 0.0012040133779264216,
                    "power_imported": 0.0012040133779264216,
                    "power_exported": 0,
                    "energy_imported": 0.0001,
                    "energy_exported": 0
                }
            },
            'hc': {'all': {'energy_exported': 0.0,
                           'energy_imported': 0.01,
                           'imported': 100,
                           'power_average': 0.12040133779264214,
                           'power_exported': 0,
                           'power_imported': 0.12040133779264214}}}
