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

SAMPLE = [{'bat': {'all': {'exported': 0, 'imported': 58.774, 'soc': 51},
          'bat2': {'exported': 0, 'imported': 61.752, 'soc': 51}},
           'counter': {'counter0': {'exported': 3.816, 'imported': 0.284}},
           'cp': {'all': {'exported': 0, 'imported': 15},
                  'cp3': {'exported': 0, 'imported': 10},
                  'cp4': {'exported': 0, 'imported': 5},
                  'cp5': {'exported': 0, 'imported': 0}},
           'date': '13:41',
           'ev': {'ev0': {'soc': 0}},
           'pv': {'all': {'exported': 88}, 'pv1': {'exported': 92}},
           "sh": {},
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
           'pv': {'all': {'exported': 214}, 'pv1': {'exported': 214}},
           "sh": {"sh1": {"temp0": 300, "temp1": 300, "temp2": 300, "imported": 100, "exported": 0}},
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
           'pv': {'all': {'exported': 339}, 'pv1': {'exported': 339}},
           "sh": {"sh1": {"temp0": 300, "temp1": 300, "temp2": 300, "imported": 200, "exported": 0}},
           'timestamp': 1654861869},
          {'bat': {'all': {'exported': 0, 'imported': 234.308, 'soc': 55},
                   'bat2': {'exported': 0, 'imported': 234.308, 'soc': 55}},
           'counter': {'counter0': {'exported': 4.921, 'imported': 1.384}},
           'cp': {'all': {'exported': 0, 'imported': 120},
                  'cp4': {'exported': 0, 'imported': 90},
                  'cp5': {'exported': 0, 'imported': 0},
                  'cp6': {'exported': 0, 'imported': 66}},
           'date': '13:51',
           'ev': {'ev0': {'soc': 6}},
           'pv': {'all': {'exported': 339}, 'pv1': {'exported': 339}},
           "sh": {"sh1": {"temp0": 300, "temp1": 300, "temp2": 300, "imported": 400, "exported": 0}},
           'timestamp': 1654862069}]

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
