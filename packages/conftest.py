import datetime
from unittest.mock import MagicMock, Mock
import pytest

from control import data
from control.bat import Bat, BatData
from control.bat import Get as BatGet
from control.bat import Set as BatSet
from control.chargepoint.chargepoint import Chargepoint, ChargepointData
from control.chargepoint.chargepoint_data import Config, Get, Set
from control.counter import Counter, CounterData
from control.counter import Config as CounterConfig
from control.counter import Get as CounterGet
from control.counter import Set as CounterSet
from control.counter_all import CounterAll
from control.pv import Pv, PvData
from control.pv import Get as PvGet
from helpermodules import hardware_configuration, pub, timecheck


@pytest.fixture(autouse=True)
def mock_open_file(monkeypatch) -> None:
    mock_config = Mock(return_value={"dc_charging": False, "openwb-version": 1, "max_c_socket": 32})
    monkeypatch.setattr(hardware_configuration, "_read_configuration", mock_config)


@pytest.fixture(autouse=True)
def mock_today(monkeypatch) -> None:
    datetime_mock = MagicMock(wraps=datetime.datetime)
    # Montag 16.05.2022, 8:40:52  "05/16/2022, 08:40:52" Unix: 1652683252
    datetime_mock.today.return_value = datetime.datetime(2022, 5, 16, 8, 40, 52)
    monkeypatch.setattr(datetime, "datetime", datetime_mock)
    mock_today_timestamp = Mock(return_value=1652683252)
    monkeypatch.setattr(timecheck, "create_timestamp", mock_today_timestamp)


@pytest.fixture(autouse=True)
def mock_pub(monkeypatch) -> Mock:
    pub_mock = Mock()
    pub_mock.pub.return_value = None
    monkeypatch.setattr(pub.Pub, 'instance', pub_mock)
    return pub_mock


def hierarchy_standard() -> CounterAll:
    # counter0
    #        |
    #        - cp3
    #        - cp4
    #        - cp5
    #        - inverter1
    #        - bat2
    # counter6
    c = CounterAll()
    c.data.get.hierarchy = [{"id": 0, "type": "counter",
                             "children": [
                                 {"id": 3, "type": "cp", "children": []},
                                 {"id": 4, "type": "cp", "children": []},
                                 {"id": 5, "type": "cp", "children": []},
                                 {"id": 1, "type": "inverter", "children": []},
                                 {"id": 2, "type": "bat", "children": []}]},
                            {"id": 6, "type": "counter", "children": []}]
    return c


def hierarchy_hybrid() -> CounterAll:
    # counter0
    #        |
    #        - cp3
    #        - cp4
    #        - cp5
    #        - inverter1
    #                  |
    #                  - bat2
    # counter6
    c = CounterAll()
    c.data.get.hierarchy = [{"id": 0, "type": "counter",
                             "children": [
                                 {"id": 3, "type": "cp", "children": []},
                                 {"id": 4, "type": "cp", "children": []},
                                 {"id": 5, "type": "cp", "children": []},
                                 {"id": 1, "type": "inverter",
                                  "children": [
                                      {"id": 2, "type": "bat", "children": []}]}]},
                            {"id": 6, "type": "counter", "children": []}]
    return c


def hierarchy_nested() -> CounterAll:
    # counter0
    #        |
    #        - cp3
    #        - counter6
    #                  |
    #                   - cp4
    #                   - cp5
    #        - inverter1
    #        - bat2
    c = CounterAll()
    c.data.get.hierarchy = [{"id": 0, "type": "counter",
                             "children": [
                                 {"id": 3, "type": "cp", "children": []},
                                 {"id": 6, "type": "counter",
                                  "children": [
                                      {"id": 4, "type": "cp", "children": []},
                                      {"id": 5, "type": "cp", "children": []}]},
                                 {"id": 1, "type": "inverter", "children": []},
                                 {"id": 2, "type": "bat", "children": []}]}]
    return c


@pytest.fixture()
def data_() -> None:
    data.data_init(Mock())
    data.data.cp_data = {
        "cp3": Mock(spec=Chargepoint, data=Mock(spec=ChargepointData,
                                                config=Mock(spec=Config, phase_1=1),
                                                get=Mock(spec=Get, currents=[30, 0, 0], power=6900,
                                                         daily_imported=10000, daily_exported=0, imported=56000,
                                                         fault_state=0),
                                                set=Mock(spec=Set, loadmanagement_available=True))),
        "cp4": Mock(spec=Chargepoint, data=Mock(spec=ChargepointData,
                                                config=Mock(spec=Config, phase_1=2),
                                                get=Mock(spec=Get, currents=[0, 15, 15], power=6900,
                                                         daily_imported=10000, daily_exported=0, imported=60000,
                                                         fault_state=0),
                                                set=Mock(spec=Set, loadmanagement_available=True))),
        "cp5": Mock(spec=Chargepoint, data=Mock(spec=ChargepointData,
                                                config=Mock(spec=Config, phase_1=3),
                                                get=Mock(spec=Get, currents=[10]*3, power=6900,
                                                         daily_imported=10000, daily_exported=0, imported=62000,
                                                         fault_state=0),
                                                set=Mock(spec=Set, loadmanagement_available=True)))}
    data.data.bat_data.update({"bat2": Mock(spec=Bat, num=2, data=Mock(spec=BatData, get=Mock(
        spec=BatGet, power=-5000, daily_imported=7000, daily_exported=3000, imported=12000, exported=10000,
        currents=None, fault_state=0),
        set=Mock(spec=BatSet, power_limit=None)))})
    data.data.pv_data.update({"pv1": Mock(spec=Pv, data=Mock(
        spec=PvData, get=Mock(spec=PvGet, power=-10000, daily_exported=6000, exported=27000, currents=None,
                              fault_state=0)))})
    data.data.counter_data.update({
        "counter0": Mock(spec=Counter, data=Mock(spec=CounterData, get=Mock(
            spec=CounterGet, currents=[40]*3, power=6200, daily_imported=45000, daily_exported=3000, fault_state=0))),
        "counter6": Mock(spec=Counter, data=Mock(spec=CounterData, get=Mock(
            spec=CounterGet, currents=[25, 10, 25], power=13800, daily_imported=20000, daily_exported=0,
            imported=14000, exported=18000, fault_state=0),
            config=Mock(spec=CounterConfig, max_currents=[32]*3),
            set=Mock(spec=CounterSet, raw_currents_left=[31]*3)))})


def hierarchy_hc_counter() -> CounterAll:
    # counter0
    #        |
    #        - counter6
    #                  |
    #                   - cp3
    #        - inverter1
    #        - bat2
    c = CounterAll()
    c.data.get.hierarchy = [{"id": 0, "type": "counter",
                             "children": [
                                 {"id": 6, "type": "counter",
                                  "children": [
                                      {"id": 3, "type": "cp", "children": []}]},
                                 {"id": 1, "type": "inverter", "children": []},
                                 {"id": 2, "type": "bat", "children": []}]}]
    return c


@pytest.fixture()
def data_hc_counter_() -> None:
    data.data_init(Mock())
    data.data.cp_data = {
        "cp3": Mock(spec=Chargepoint, data=Mock(spec=ChargepointData,
                                                config=Mock(spec=Config, phase_1=1),
                                                get=Mock(spec=Get, currents=[30, 0, 0], power=6900,
                                                         daily_imported=10000, daily_exported=0, imported=56000,
                                                         fault_state=0),
                                                set=Mock(spec=Set, loadmanagement_available=True)))}
    data.data.pv_data.update({"pv1": Mock(spec=Pv, data=Mock(
        spec=PvData, get=Mock(spec=PvGet, power=-10000, daily_exported=6000, exported=27000, currents=None,
                              fault_state=0)))})
    data.data.counter_data.update({
        "counter0": Mock(spec=Counter, data=Mock(spec=CounterData, get=Mock(
            spec=CounterGet, currents=[40]*3, power=-2000, daily_imported=45000, daily_exported=3000, fault_state=0))),
        "counter6": Mock(spec=Counter, data=Mock(spec=CounterData, get=Mock(
            spec=CounterGet, currents=[25, 10, 25], power=8000, daily_imported=20000, daily_exported=0,
            imported=14000, exported=18000, fault_state=0),
            config=Mock(spec=CounterConfig, max_currents=[32]*3),
            set=Mock(spec=CounterSet, raw_currents_left=[31]*3)))})
