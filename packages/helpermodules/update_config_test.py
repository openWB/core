import datetime
from unittest.mock import Mock, mock_open

import pytest
from helpermodules import update_config
from helpermodules.update_config import UpdateConfig
from modules.electricity_tariffs.awattar import tariff
from test_utils.test_environment import running_on_github


ALL_RECEIVED_TOPICS = {
    'openWB/chargepoint/5/get/voltages': b'[230.2,230.2,230.2]',
    'openWB/chargepoint/3/get/state_str': b'"Keine Ladung, da kein Auto angesteckt ist."',
    'openWB/chargepoint/3/config': (b'{"name": "Standard-Ladepunkt", "type": "mqtt", "ev": 0, "template": 0,'
                                    b'"connected_phases": 3, "phase_1": 1, "auto_phase_switch_hw": false, '
                                    b'"control_pilot_interruption_hw": false, "id": 3, "connection_module": '
                                    b'{"type": "mqtt", "name": "MQTT-Ladepunkt", "configuration": {}}, '
                                    b'"power_module": {}}'),
    'openWB/chargepoint/get/power': b'0',
    'openWB/chargepoint/template/0': (b'{"autolock": {"active": false, "plans": {}, "wait_for_charging_end": false}, '
                                      b'"name": "Standard Ladepunkt-Profil" '
                                      b'"valid_tags": [], "id": 0}'),
    'openWB/optional/int_display/theme': b'"cards"'}


def test_remove_invalid_topics(mock_pub):
    # setup
    update_config = UpdateConfig()
    update_config.all_received_topics = ALL_RECEIVED_TOPICS

    # execution
    update_config._remove_invalid_topics()

    # evaluation
    assert len(mock_pub.method_calls) == 2
    assert mock_pub.method_calls[0][1][0] == 'openWB/chargepoint/5/get/voltages'
    assert mock_pub.method_calls[1][1][0] == 'openWB/optional/int_display/theme'


def create_daily_log_with_charging(date: str, num_of_intervalls, passed_intervals: int = 0):
    bat_imported = counter_exported = 0
    bat_exported = passed_intervals * 1000
    pv_exported = passed_intervals * 500
    cp_imported = passed_intervals * 2000
    counter_imported = passed_intervals * 500
    date = datetime.datetime.strptime(date, "%m/%d/%Y, %H:%M")
    daily_log = {"entries": []}
    for i in range(0, num_of_intervalls):
        if i != 0 and i != num_of_intervalls - 1:
            bat_exported += 1000
            pv_exported += 500
            cp_imported += 2000
            counter_imported += 500
        daily_log["entries"].append({'bat': {'all': {'exported': bat_exported, 'imported': bat_imported, 'soc': 100},
                                             'bat2': {'exported': bat_exported, 'imported': bat_imported, 'soc': 100}},
                                     'counter': {'counter0': {'exported': counter_exported,
                                                              'grid': True,
                                                              'imported': counter_imported}},
                                     'cp': {'all': {'exported': 0, 'imported': cp_imported},
                                            'cp4': {'exported': 0, 'imported': cp_imported}},
                                     'date': date.strftime("%H:%M"),
                                     'ev': {'ev0': {'soc': None}},
                                     'hc': {'all': {'imported': 0}},
                                     'pv': {'all': {'exported': pv_exported}, 'pv1': {'exported': pv_exported}},
                                     'sh': {},
                                     'timestamp': date.timestamp()})
        date += datetime.timedelta(minutes=5)
    return daily_log


chargelog_no_hour_change = [{'chargepoint': {'id': 4, 'name': 'LP 1'},
                             'data': {'costs': 1.5,
                                      'imported_since_mode_switch': 6000,
                                      'imported_since_plugged': 6000,
                                      'power': 22,
                                      'range_charged': 45.65},
                             'time': {'begin': '01/03/2024, 10:27:50',
                                      'end': '01/03/2024, 10:43:58',
                                      'time_charged': '1:50'},
                             'vehicle': {'chargemode': 'instant_charging',
                                         'id': 13,
                                         'name': 'Fahrzeug 1',
                                         'prio': False,
                                         'rfid': None}}]
chargelog_one_hour_change = [{'chargepoint': {'id': 4, 'name': 'LP 1'},
                              'data': {'costs': 1.5,
                                       'imported_since_mode_switch': 6000,
                                       'imported_since_plugged': 6000,
                                       'power': 22,
                                       'range_charged': 145.24},
                              'time': {'begin': '01/03/2024, 10:57:58',
                                       'end': '01/03/2024, 11:06:56',
                                       'time_charged': '4:28'},
                              'vehicle': {'chargemode': 'scheduled_charging',
                                          'id': 13,
                                          'name': 'Fahrzeug 1',
                                          'prio': False,
                                          'rfid': None}}]
chargelog_one_hour_change_bug = [{'chargepoint': {'id': 4, 'name': 'LP 1'},
                                  'data': {'costs': 2.3,
                                           'imported_since_mode_switch': 6000,
                                           'imported_since_plugged': 6000,
                                           'power': 22,
                                           'range_charged': 145.24},
                                  'time': {'begin': '01/03/2024, 10:57:58',
                                           'end': '01/03/2024, 11:06:56',
                                           'time_charged': '4:28'},
                                  'vehicle': {'chargemode': 'scheduled_charging',
                                              'id': 13,
                                              'name': 'Fahrzeug 1',
                                              'prio': False,
                                              'rfid': None}}]
chargelog_one_hour_change_day_change_bug = [{'chargepoint': {'id': 4, 'name': 'LP 1'},
                                             'data': {'costs': 2.3,
                                                      'imported_since_mode_switch': 6000,
                                                      'imported_since_plugged': 6000,
                                                      'power': 22,
                                                      'range_charged': 145.24},
                                             'time': {'begin': '01/03/2024, 23:57:58',
                                                      'end': '01/04/2024, 00:06:56',
                                                      'time_charged': '4:28'},
                                             'vehicle': {'chargemode': 'scheduled_charging',
                                                         'id': 13,
                                                         'name': 'Fahrzeug 1',
                                                         'prio': False,
                                                         'rfid': None}}]
chargelog_two_hour_change = [{'chargepoint': {'id': 4, 'name': 'LP 1'},
                              'data': {'costs': 7.4,
                                       'imported_since_mode_switch': 24692.0,
                                       'imported_since_plugged': 32453.0,
                                       'power': 1.53,
                                       'range_charged': 145.24},
                              'time': {'begin': '01/03/2024, 10:53:58',
                                       'end': '01/03/2024, 12:02:56',
                                       'time_charged': '4:28'},
                              'vehicle': {'chargemode': 'scheduled_charging',
                                          'id': 13,
                                          'name': 'Fahrzeug 1',
                                          'prio': False,
                                          'rfid': None}}]


@pytest.mark.parametrize("load, expected_call_count, expected_costs", [
    pytest.param([chargelog_no_hour_change], 0, 0, id=" innerhalb einer Stunde"),
    pytest.param([chargelog_one_hour_change_bug, create_daily_log_with_charging(
        "01/03/2024, 10:55", 5), create_daily_log_with_charging(
        "01/03/2024, 10:55", 5)], 1, 1.2000000000000002, id="ein Stundenwechsel, Bugfix"),
    pytest.param([chargelog_one_hour_change_day_change_bug, create_daily_log_with_charging(
        "01/03/2024, 23:55", 1), create_daily_log_with_charging(
        "01/04/2024, 00:00", 4, 1), create_daily_log_with_charging(
        "01/04/2024, 00:00", 4, 1), create_daily_log_with_charging(
        "01/04/2024, 00:00", 4, 1)], 1, 1.2000000000000002, id="ein Stundenwechsel, ein Tageswechsel, Bugfix"),
    pytest.param([chargelog_one_hour_change], 0, 0, id="ein Stundenwechsel, kein Bugfix nötig"),
    pytest.param([chargelog_two_hour_change], 0, 0, id="zwei Stundenwechsel"),
]
)
def test_upgrade_datastore_52(load, expected_call_count, expected_costs, monkeypatch):
    for _ in range(7):
        load.append(FileNotFoundError())
    mock_json_load = Mock(side_effect=load)
    monkeypatch.setattr(update_config.json, "load", mock_json_load)
    mock_json_dump = Mock()
    monkeypatch.setattr(update_config.json, "dump", mock_json_dump)
    m_open = mock_open()
    monkeypatch.setattr("builtins.open", m_open)
    mock_copyfile = Mock()
    monkeypatch.setattr(update_config, "copyfile", mock_copyfile)
    u = UpdateConfig()
    u.all_received_topics = {"openWB/general/prices/bat": b'0.0002',
                             "openWB/general/prices/grid": b'0.0003',
                             "openWB/general/prices/pv": b'0.0001',
                             "openWB/optional/et/provider": b'{"type": null, "configuration": {}}'}

    u.upgrade_datastore_52()

    assert mock_json_dump.call_count == expected_call_count
    if expected_call_count > 0:
        assert mock_json_dump.call_args[0][0][0]['data']['costs'] == expected_costs


def test_upgrade_datastore_52_with_tariff(monkeypatch):
    if running_on_github():
        # ToDo Zeitzonen berücksichtigen, damit Tests auf Github laufen
        return
    load = [chargelog_one_hour_change_day_change_bug, create_daily_log_with_charging(
        "01/03/2024, 23:55", 1)] + [create_daily_log_with_charging(
            "01/04/2024, 00:00", 4, 1)] * 3
    for _ in range(7):
        load.append(FileNotFoundError())
    mock_json_load = Mock(side_effect=load)
    monkeypatch.setattr(update_config.json, "load", mock_json_load)
    mock_json_dump = Mock()
    monkeypatch.setattr(update_config.json, "dump", mock_json_dump)
    m_open = mock_open()
    monkeypatch.setattr("builtins.open", m_open)
    mock_copyfile = Mock()
    monkeypatch.setattr(update_config, "copyfile", mock_copyfile)
    # Mock auskommentieren, um echte Daten zu erhalten
    mock_awattar = Mock(return_value={1704319200: 5.812e-05, 1704322800: 5.73e-05, 1704326400: 5.046e-05})
    monkeypatch.setattr(tariff, "fetch_prices", mock_awattar)
    u = UpdateConfig()
    u.all_received_topics = {"openWB/general/prices/bat": b'0.0002',
                             "openWB/general/prices/grid": b'0.0003',
                             "openWB/general/prices/pv": b'0.0001',
                             "openWB/optional/et/provider":
                             b'{"name": "aWATTar Hourly", "type": "awattar", "configuration": {"country": "de"}}'}

    u.upgrade_datastore_52()

    assert mock_json_dump.call_count == 1
    assert mock_json_dump.call_args[0][0][0]['data']['costs'] == 0.8364
