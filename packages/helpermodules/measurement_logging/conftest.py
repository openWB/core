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


EXPECTED = {
    "openWB/set/bat/get/daily_imported": 175.534,
    "openWB/set/bat/get/daily_exported": 0,
    "openWB/set/bat/2/get/daily_imported": 172.556,
    "openWB/set/bat/2/get/daily_exported": 0,
    "openWB/set/counter/0/get/daily_imported": 1.1,
    "openWB/set/counter/0/get/daily_exported": 1.105,
    "openWB/set/chargepoint/get/daily_imported": 105,
    "openWB/set/chargepoint/get/daily_exported": 0,
    "openWB/set/chargepoint/4/get/daily_imported": 85,
    "openWB/set/chargepoint/4/get/daily_exported": 0,
    "openWB/set/chargepoint/5/get/daily_imported": 0,
    "openWB/set/chargepoint/5/get/daily_exported": 0,
    "openWB/set/chargepoint/6/get/daily_imported": 2,
    "openWB/set/chargepoint/6/get/daily_exported": 0,
    "openWB/set/pv/get/daily_exported": 251,
    "openWB/set/pv/1/get/daily_exported": 247}

SAMPLE = [{"timestamp": 1690529761,
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
           "sh": {"sh1": {"temp0": 300, "temp1": 300, "temp2": 300, "imported": 0.1, "exported": 0}}},
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
           "sh": {"sh1": {"temp0": 300, "temp1": 300, "temp2": 300, "imported": 0.2, "exported": 0}}},
          {"timestamp": 1690530360,
           "date": "09:45",
           "cp": {
               "cp3": {"imported": 4772.491, "exported": 0},
               "cp5": {"imported": 1592.81, "exported": 0},
               "cp4": {"imported": 1582.508, "exported": 0},
               "all": {"imported": 7947.808999999999, "exported": 0}},
           "ev": {"ev0": {"soc": 0}},
           "counter": {"counter0": {"imported": 6178.065, "exported": 2.396, "grid": True}},
           "pv": {"pv1": {"exported": 1055}, "all": {"exported": 1055}},
           "bat": {"bat2": {"imported": 2.42, "exported": 2292.992, "soc": 4},
                   "all": {"imported": 2.42, "exported": 2292.992, "soc": 4}},
           "sh": {"sh1": {"temp0": 300, "temp1": 300, "temp2": 300, "imported": 0.4, "exported": 0}}}
          ]

TOTALS = {'bat': {'all': {'exported': 0, 'imported': 175.534},
          'bat2': {'exported': 0, 'imported': 172.556}},
          'counter': {'counter0': {'exported': 1.105, 'imported': 1.1}},
          'cp': {'all': {'exported': 0, 'imported': 105},
                 'cp3': {'exported': 0, 'imported': 10},
                 'cp4': {'exported': 0, 'imported': 85},
                 'cp5': {'exported': 0, 'imported': 0},
                 'cp6': {'exported': 0, 'imported': 2}},
          'pv': {'all': {'exported': 251}, 'pv1': {'exported': 247}},
          "sh": {"sh1": {"imported": 300, "exported": 0}}}

NAMES = {'bat2': "Speicher",
         'counter0': "Zähler",
         'cp3': "cp3",
         'cp4': "Standard-Ladepunkt",
         'cp5': "Standard-Ladepunkt",
         'cp6': "Standard-Ladepunkt",
         'pv1': "Wechselrichter",
         "sh1": "Smarthome1"}

POWER_SOURCE_TOTALS = {'bat': {'all': {'exported': 0, 'imported': 175.534},
                               'bat2': {'exported': 0, 'imported': 172.556}},
                       'counter': {'counter0': {'exported': 1.105, 'imported': 1.1}},
                       'cp': {'all': {'exported': 0, 'imported': 105},
                              'cp3': {'exported': 0, 'imported': 10},
                              'cp4': {'exported': 0, 'imported': 85},
                              'cp5': {'exported': 0, 'imported': 0},
                              'cp6': {'exported': 0, 'imported': 2}},
                       'pv': {'all': {'exported': 251}, 'pv1': {'exported': 247}},
                       "sh": {"sh1": {"imported": 300, "exported": 0}},
                       "power_source": {"grid": 1.46, "pv": 0, "bat": 0, "cp": 0}}
