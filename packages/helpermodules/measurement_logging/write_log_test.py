from unittest.mock import Mock
import json

from helpermodules.measurement_logging import write_log
from helpermodules.measurement_logging.write_log import get_names


def test_get_names(daily_log_totals, monkeypatch):
    # setup
    component_names_mock = Mock(side_effect=["Speicher", "Zähler", "Wechselrichter"])
    monkeypatch.setattr(write_log, "get_component_name_by_id", component_names_mock)
    # execution
    names = get_names(daily_log_totals, {"sh1": "Smarthome1"})

    # evaluation
    assert names == {'bat2': "Speicher",
                     "consumer6": "MQTT-Verbraucher",
                     'counter0': "Zähler",
                     'cp3': "cp3",
                     'cp4': "neuer Ladepunkt",
                     'cp5': "neuer Ladepunkt",
                     'cp6': "neuer Ladepunkt",
                     'pv1': "Wechselrichter",
                     "sh1": "Smarthome1"}


def test_fix_values():
    # setup
    previous_entry = {'bat': {'all': {'exported': 0, 'imported': 2281.851, 'soc': 96},
                              'bat2': {'exported': 0, 'imported': 2281.851, 'soc': 96}},
                      'counter': {'counter0': {'exported': 21.382,
                                               'grid': True,
                                               'imported': 17.913}},
                      'cp': {'all': {'exported': 0, 'imported': 0},
                             'cp3': {'exported': 0, 'imported': 0},
                             'cp4': {'exported': 0, 'imported': 0},
                             'cp5': {'exported': 0, 'imported': 0}},
                      'date': '09:25',
                      'ev': {'ev0': {'soc': 0}},
                      'hc': {'all': {'imported': 108647.2791628165}},
                      'pv': {'all': {'exported': 3269}, 'pv1': {'exported': 3269}},
                      'sh': {},
                      'timestamp': 1709108702}
    new_entry = {'bat': {'all': {'exported': 0, 'imported': 2369.658, 'soc': 97},
                         'bat2': {'exported': 0, 'imported': 2369.658, 'soc': 97}},
                 'counter': {'counter0': {'exported': 22.167, 'grid': True, 'imported': 18.54}},
                 'cp': {'all': {'exported': 0, 'imported': 0},
                        'cp3': {'exported': 0, 'imported': 0},
                        'cp4': {'exported': 0, 'imported': 0},
                        'cp5': {'exported': 0, 'imported': 0}},
                 'date': '09:30',
                 'ev': {'ev0': {'soc': 0}},
                 'hc': {'all': {'imported': 108683.21291147666}},
                 'pv': {'all': {'exported': 0}, 'pv1': {'exported': 0}},
                 'sh': {},
                 'timestamp': 1709109001}

    # execution
    fixed_values = write_log.fix_values(new_entry, previous_entry)

    # evaluation
    assert fixed_values == {'bat': {'all': {'exported': 0, 'imported': 2369.658, 'soc': 97},
                                    'bat2': {'exported': 0, 'imported': 2369.658, 'soc': 97}},
                            'counter': {'counter0': {'exported': 22.167, 'grid': True, 'imported': 18.54}},
                            'cp': {'all': {'exported': 0, 'imported': 0},
                                   'cp3': {'exported': 0, 'imported': 0},
                                   'cp4': {'exported': 0, 'imported': 0},
                                   'cp5': {'exported': 0, 'imported': 0}},
                            'date': '09:30',
                            'ev': {'ev0': {'soc': 0}},
                            'hc': {'all': {'imported': 108683.21291147666}},
                            'pv': {'all': {'exported': 3269}, 'pv1': {'exported': 3269}},
                            'sh': {},
                            'timestamp': 1709109001}


def test_fix_values_missing_components():
    # setup
    previous_entry = {'bat': {'all': {'exported': 0, 'imported': 2281.851, 'soc': 96},
                              'bat2': {'exported': 0, 'imported': 2281.851, 'soc': 96}},
                      'counter': {'counter0': {'exported': 21.382,
                                               'grid': True,
                                               'imported': 17.913}},
                      'cp': {'all': {'exported': 0, 'imported': 0},
                             'cp3': {'exported': 0, 'imported': 0},
                             'cp4': {'exported': 0, 'imported': 0},
                             'cp5': {'exported': 0, 'imported': 0}},
                      'date': '09:25',
                      'ev': {'ev0': {'soc': 0}},
                      'hc': {'all': {'imported': 108647.2791628165}},
                      'pv': {'all': {'exported': 3269}},
                      'sh': {},
                      'timestamp': 1709108702}
    new_entry = {'bat': {'all': {'exported': 0, 'imported': 2369.658, 'soc': 97},
                         'bat2': {'exported': 0, 'imported': 2369.658, 'soc': 97}},
                 'counter': {'counter0': {'exported': 22.167, 'grid': True, 'imported': 18.54}},
                 'cp': {'all': {'exported': 0, 'imported': 0},
                        'cp3': {'exported': 0, 'imported': 0},
                        'cp4': {'exported': 0, 'imported': 0},
                        'cp5': {'exported': 0, 'imported': 0}},
                 'date': '09:30',
                 'ev': {'ev0': {'soc': 0}},
                 'hc': {'all': {'imported': 108683.21291147666}},
                 'pv': {'all': {'exported': 0}, 'pv1': {'exported': 0}},
                 'sh': {},
                 'timestamp': 1709109001}

    # execution
    fixed_values = write_log.fix_values(new_entry, previous_entry)

    # evaluation
    assert fixed_values == {'bat': {'all': {'exported': 0, 'imported': 2369.658, 'soc': 97},
                                    'bat2': {'exported': 0, 'imported': 2369.658, 'soc': 97}},
                            'counter': {'counter0': {'exported': 22.167, 'grid': True, 'imported': 18.54}},
                            'cp': {'all': {'exported': 0, 'imported': 0},
                                   'cp3': {'exported': 0, 'imported': 0},
                                   'cp4': {'exported': 0, 'imported': 0},
                                   'cp5': {'exported': 0, 'imported': 0}},
                            'date': '09:30',
                            'ev': {'ev0': {'soc': 0}},
                            'hc': {'all': {'imported': 108683.21291147666}},
                            'pv': {'all': {'exported': 3269}, 'pv1': {'exported': 0}},
                            'sh': {},
                            'timestamp': 1709109001}


def test_save_log_keeps_existing_names_and_colors_when_writing_new_entry(monkeypatch):
    # setup
    existing_content = {
        "entries": [{"timestamp": 1, "cp": {"cp1": {"imported": 1, "exported": 0}}}],
        "names": {"cp1": "Bestehender Ladepunkt"},
        "colors": {"cp1": "#111111"},
    }
    mocked_file = Mock()
    mocked_file.__enter__ = Mock(return_value=mocked_file)
    mocked_file.__exit__ = Mock(return_value=None)
    mocked_file.read = Mock(return_value=json.dumps(existing_content))
    monkeypatch.setattr("builtins.open", Mock(return_value=mocked_file))
    monkeypatch.setattr(write_log.timecheck, "create_timestamp_YYYYMMDD", Mock(return_value="20261002"))
    monkeypatch.setattr(write_log, "get_previous_entry", Mock(return_value=existing_content["entries"][-1]))
    monkeypatch.setattr(write_log, "LegacySmartHomeLogData", Mock(return_value=Mock(sh_names={}, sh_dict={})))

    new_entry = {"timestamp": 2, "cp": {"cp2": {"imported": 2, "exported": 0}}}
    monkeypatch.setattr(write_log, "create_entry", Mock(return_value=new_entry))
    monkeypatch.setattr(write_log, "get_names", Mock(
        return_value={"cp1": "Bestehender Ladepunkt", "cp2": "Neuer Ladepunkt"}))
    monkeypatch.setattr(write_log, "get_colors", Mock(return_value={"cp1": "#111111", "cp2": "#222222"}))
    write_and_check_mock = Mock()
    monkeypatch.setattr(write_log, "write_and_check", write_and_check_mock)

    # execution
    write_log.save_log()

    # evaluation
    written_content = write_and_check_mock.call_args.args[1]
    assert written_content["names"] == {
        "cp1": "Bestehender Ladepunkt",
        "cp2": "Neuer Ladepunkt",
    }
    assert written_content["colors"] == {
        "cp1": "#111111",
        "cp2": "#222222",
    }
