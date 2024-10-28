from unittest.mock import Mock
import pytest

from modules.common.abstract_vehicle import CalculatedSocState, GeneralVehicleConfig, VehicleUpdateData
from modules.common.component_state import CarState
from modules.common.configurable_vehicle import ConfigurableVehicle, SocSource
from modules.common import store
from modules.devices.tesla.tesla.config import Tesla
from modules.vehicles.common.calc_soc import calc_soc
from modules.vehicles.manual.config import ManualSoc
from modules.vehicles.mqtt.config import MqttSocSetup

TIMESTAMP_SOC_VALID = 1652683202
TIMESTAMP_SOC_INVALID = 1652682880


def conf_vehicle_manual_from_cp():
    component_updater_mock = Mock(return_value=CarState(soc=42))
    general_config = GeneralVehicleConfig(use_soc_from_cp=True)
    calculated_soc_state = CalculatedSocState()
    return ConfigurableVehicle(vehicle_config=ManualSoc(),
                               component_updater=component_updater_mock,
                               vehicle=0,
                               calc_while_charging=False,
                               general_config=general_config,
                               calculated_soc_state=calculated_soc_state)


def conf_vehicle_manual():
    component_updater_mock = Mock(return_value=CarState(soc=42))
    general_config = GeneralVehicleConfig(use_soc_from_cp=False)
    calculated_soc_state = CalculatedSocState()
    return ConfigurableVehicle(vehicle_config=ManualSoc(),
                               component_updater=component_updater_mock,
                               vehicle=0,
                               calc_while_charging=False,
                               general_config=general_config,
                               calculated_soc_state=calculated_soc_state)


def conf_vehicle_api_from_cp():
    component_updater_mock = Mock(return_value=CarState(soc=42))
    general_config = GeneralVehicleConfig(use_soc_from_cp=True)
    calculated_soc_state = CalculatedSocState()
    return ConfigurableVehicle(vehicle_config=Tesla(),
                               component_updater=component_updater_mock,
                               vehicle=0,
                               calc_while_charging=False,
                               general_config=general_config,
                               calculated_soc_state=calculated_soc_state)


def conf_vehicle_api():
    component_updater_mock = Mock(return_value=CarState(soc=42))
    general_config = GeneralVehicleConfig(use_soc_from_cp=False)
    calculated_soc_state = CalculatedSocState()
    return ConfigurableVehicle(vehicle_config=Tesla(),
                               component_updater=component_updater_mock,
                               vehicle=0,
                               calc_while_charging=False,
                               general_config=general_config,
                               calculated_soc_state=calculated_soc_state)


def conf_vehicle_api_while_charging():
    component_updater_mock = Mock(return_value=CarState(soc=42))
    general_config = GeneralVehicleConfig(use_soc_from_cp=False)
    calculated_soc_state = CalculatedSocState()
    return ConfigurableVehicle(vehicle_config=Tesla(),
                               component_updater=component_updater_mock,
                               vehicle=0,
                               calc_while_charging=True,
                               general_config=general_config,
                               calculated_soc_state=calculated_soc_state)


def conf_vehicle_mqtt():
    component_updater_mock = Mock()
    general_config = GeneralVehicleConfig(use_soc_from_cp=False)
    calculated_soc_state = CalculatedSocState()
    return ConfigurableVehicle(vehicle_config=MqttSocSetup(),
                               component_updater=component_updater_mock,
                               vehicle=0,
                               calc_while_charging=False,
                               general_config=general_config,
                               calculated_soc_state=calculated_soc_state)


@pytest.mark.parametrize(
    "conf_vehicle, use_soc_from_cp, vehicle_update_data, calculated_soc_state, expected_source",
    [
        pytest.param(conf_vehicle_manual(), False, VehicleUpdateData(), CalculatedSocState(
            manual_soc=34), SocSource.MANUAL, id="Manuell, neuer Start-SoC"),
        pytest.param(conf_vehicle_manual(), False, VehicleUpdateData(plug_state=True), CalculatedSocState(
            soc_start=34), SocSource.CALCULATION, id="Manuell berechnen"),
        pytest.param(conf_vehicle_manual(), False, VehicleUpdateData(), CalculatedSocState(
            soc_start=34), SocSource.NO_UPDATE, id="Manuell nicht aktualisieren, da nicht angesteckt"),
        pytest.param(conf_vehicle_manual_from_cp(), True,
                     VehicleUpdateData(soc_from_cp=45, timestamp_soc_from_cp=TIMESTAMP_SOC_INVALID),
                     CalculatedSocState(manual_soc=34), SocSource.MANUAL, id="Manuell mit SoC vom LP, neuer Start-SoC"),
        pytest.param(conf_vehicle_manual_from_cp(), True,
                     VehicleUpdateData(soc_from_cp=45, timestamp_soc_from_cp=TIMESTAMP_SOC_VALID),
                     CalculatedSocState(soc_start=34), SocSource.CP, id="Manuell mit SoC vom LP, neuer LP-SoC"),
        pytest.param(conf_vehicle_manual_from_cp(), True,
                     VehicleUpdateData(soc_from_cp=45, timestamp_soc_from_cp=TIMESTAMP_SOC_INVALID),
                     CalculatedSocState(soc_start=34), SocSource.CALCULATION,
                     id="Manuell mit SoC vom LP, LP-SoC berechnen"),
        pytest.param(conf_vehicle_api(), True, VehicleUpdateData(), CalculatedSocState(), SocSource.API, id="API"),
        pytest.param(conf_vehicle_api_from_cp(), True, VehicleUpdateData(
            soc_from_cp=45, timestamp_soc_from_cp=TIMESTAMP_SOC_VALID), CalculatedSocState(), SocSource.CP,
            id="API mit SoC vom LP, neuer LP-SoC"),
        pytest.param(conf_vehicle_api_from_cp(),  True, VehicleUpdateData(soc_from_cp=None),
                     CalculatedSocState(), SocSource.API, id="API mit SoC vom LP, kein LP-SoC"),
        pytest.param(conf_vehicle_api_from_cp(),  True,
                     VehicleUpdateData(soc_from_cp=45, timestamp_soc_from_cp=TIMESTAMP_SOC_INVALID),
                     CalculatedSocState(soc_start=34), SocSource.CALCULATION,
                     id="API mit SoC vom LP, LP-SoC berechnen"),
        pytest.param(conf_vehicle_api_while_charging(), False, VehicleUpdateData(),
                     CalculatedSocState(), SocSource.API, id="API mit Berechnung, keine Ladung"),
        pytest.param(conf_vehicle_api_while_charging(), False, VehicleUpdateData(plug_state=True,
                     charge_state=True), CalculatedSocState(), SocSource.CALCULATION, id="API mit Berechnung, Ladung"),
        pytest.param(conf_vehicle_mqtt(), False, VehicleUpdateData(plug_state=True),
                     CalculatedSocState(), SocSource.NO_UPDATE, id="Kein Update, da Werte per MQTT"),
    ])
def test_get_carstate_source(conf_vehicle: ConfigurableVehicle,
                             use_soc_from_cp,
                             vehicle_update_data,
                             calculated_soc_state,
                             expected_source):
    # setup
    conf_vehicle.general_config.use_soc_from_cp = use_soc_from_cp
    conf_vehicle.calculated_soc_state = calculated_soc_state
    # execution
    source = conf_vehicle._get_carstate_source(vehicle_update_data)

    # evaluation
    assert source == expected_source


# awkward tests
@pytest.mark.parametrize(
    "vehicle_update_data, use_soc_from_cp, expected_calculated_soc_state, expected_call_count",
    [
        pytest.param(VehicleUpdateData(), False, CalculatedSocState(soc_start=42), 1, id="request only from api"),
        pytest.param(VehicleUpdateData(imported=150), True, CalculatedSocState(
            soc_start=42, imported_start=150), 1, id="request from api, not plugged"),
        pytest.param(VehicleUpdateData(imported=200, plug_state=True), True, CalculatedSocState(
            soc_start=42, imported_start=200), 1, id="request from api, recently plugged"),
    ])
def test_update_api(vehicle_update_data,
                    use_soc_from_cp,
                    expected_calculated_soc_state,
                    expected_call_count,
                    monkeypatch):
    # setup
    mock_value_store = Mock(name="value_store")
    monkeypatch.setattr(store, "get_car_value_store", Mock(return_value=mock_value_store))
    component_updater_mock = Mock(return_value=CarState(soc=42))
    general_config = GeneralVehicleConfig(use_soc_from_cp=use_soc_from_cp)
    calculated_soc_state = CalculatedSocState()
    c = ConfigurableVehicle(vehicle_config=Tesla(),
                            component_updater=component_updater_mock,
                            vehicle=0,
                            calc_while_charging=False,
                            general_config=general_config,
                            calculated_soc_state=calculated_soc_state)
    vehicle_update_data = vehicle_update_data

    # execution
    c.update(vehicle_update_data)

    # evaluation
    assert mock_value_store.set.call_count == expected_call_count
    if expected_call_count >= 1:
        assert mock_value_store.set.call_args[0][0].soc == 42
    assert c.calculated_soc_state == expected_calculated_soc_state


def test_1(monkeypatch):
    # Eintragen -> Anstecken -> aktueller SoC von EV -> SoC von Ev hochrechnen
    # setup
    mock_value_store = Mock(name="value_store")
    monkeypatch.setattr(store, "get_car_value_store", Mock(return_value=mock_value_store))
    c = conf_vehicle_manual_from_cp()
    c.calculated_soc_state = CalculatedSocState(manual_soc=42)

    # execution
    c.update(VehicleUpdateData())
    c.update(VehicleUpdateData(plug_state=True))
    c.update(VehicleUpdateData(plug_state=True, soc_from_cp=45, timestamp_soc_from_cp=TIMESTAMP_SOC_VALID))

    # evaluation
    assert mock_value_store.set.call_args[0][0].soc == 45
    assert c.calculated_soc_state == CalculatedSocState(manual_soc=None, soc_start=45)


def test_2(monkeypatch):
    # Anstecken -> Eintragen -> aktueller SoC von EV -> SoC von Ev hochrechnen
    # setup
    mock_calc_soc = Mock(name="calc_soc", return_value=47)
    monkeypatch.setattr(calc_soc, "calc_soc", mock_calc_soc)
    mock_value_store = Mock(name="value_store")
    monkeypatch.setattr(store, "get_car_value_store", Mock(return_value=mock_value_store))
    c = conf_vehicle_manual_from_cp()

    # execution
    c.update(VehicleUpdateData(plug_state=True))
    c.calculated_soc_state.manual_soc = 42
    c.update(VehicleUpdateData(plug_state=True))
    c.update(VehicleUpdateData(plug_state=True, soc_from_cp=45, timestamp_soc_from_cp=TIMESTAMP_SOC_VALID))
    # im nächsten Zyklus wird mit calc_soc hochgerechnet
    c.update(VehicleUpdateData(plug_state=True, soc_from_cp=45, timestamp_soc_from_cp=TIMESTAMP_SOC_INVALID))

    # evaluation
    assert mock_value_store.set.call_args_list[3][0][0].soc == 47
    assert mock_calc_soc.call_args[0][3] == 45  # soc
    assert c.calculated_soc_state == CalculatedSocState(manual_soc=None, soc_start=45)


def test_3(monkeypatch):
    # Anstecken -> aktueller SoC von EV -> Eintragen -> Manuellen SoC hochrechnen
    # setup
    mock_calc_soc = Mock(name="calc_soc", return_value=44)
    monkeypatch.setattr(calc_soc, "calc_soc", mock_calc_soc)
    mock_value_store = Mock(name="value_store")
    monkeypatch.setattr(store, "get_car_value_store", Mock(return_value=mock_value_store))
    c = conf_vehicle_manual_from_cp()

    # execution
    c.update(VehicleUpdateData(plug_state=True))
    c.update(VehicleUpdateData(plug_state=True, soc_from_cp=45, timestamp_soc_from_cp=TIMESTAMP_SOC_VALID))
    c.calculated_soc_state.manual_soc = 42
    c.update(VehicleUpdateData(plug_state=True, soc_from_cp=45, timestamp_soc_from_cp=TIMESTAMP_SOC_INVALID))
    # im nächsten Zyklus wird mit calc_soc hochgerechnet
    c.update(VehicleUpdateData(plug_state=True, soc_from_cp=45, timestamp_soc_from_cp=TIMESTAMP_SOC_INVALID))

    # evaluation
    assert mock_value_store.set.call_args_list[3][0][0].soc == 44
    assert mock_calc_soc.call_count == 2
    assert c.calculated_soc_state == CalculatedSocState(manual_soc=None, soc_start=42)


def test_4(monkeypatch):
    # Anstecken -> kein SoC von EV -> Eintragen -> Manuellen SoC hochrechnen
    # setup
    mock_calc_soc = Mock(name="calc_soc", return_value=44)
    monkeypatch.setattr(calc_soc, "calc_soc", mock_calc_soc)
    mock_value_store = Mock(name="value_store")
    monkeypatch.setattr(store, "get_car_value_store", Mock(return_value=mock_value_store))
    c = conf_vehicle_manual_from_cp()

    # execution
    c.update(VehicleUpdateData(plug_state=True))
    c.calculated_soc_state.manual_soc = 42
    c.update(VehicleUpdateData(plug_state=True))
    # im nächsten Zyklus wird mit calc_soc hochgerechnet
    c.update(VehicleUpdateData(plug_state=True))

    # evaluation
    assert mock_value_store.set.call_args_list[2][0][0].soc == 44
    assert mock_calc_soc.call_count == 2
    assert c.calculated_soc_state == CalculatedSocState(manual_soc=None, soc_start=42)


def test_5(monkeypatch):
    # Anstecken -> kein aktueller SoC von EV -> Eintragen -> Manuellen SoC hochrechnen
    # setup
    mock_calc_soc = Mock(name="calc_soc", return_value=44)
    monkeypatch.setattr(calc_soc, "calc_soc", mock_calc_soc)
    mock_value_store = Mock(name="value_store")
    monkeypatch.setattr(store, "get_car_value_store", Mock(return_value=mock_value_store))
    c = conf_vehicle_manual_from_cp()

    # execution
    c.update(VehicleUpdateData(plug_state=True, soc_from_cp=45, timestamp_soc_from_cp=TIMESTAMP_SOC_VALID))
    c.calculated_soc_state.manual_soc = 42
    c.update(VehicleUpdateData(plug_state=True))
    # im nächsten Zyklus wird mit calc_soc hochgerechnet
    c.update(VehicleUpdateData(plug_state=True))

    # evaluation
    assert mock_value_store.set.call_args_list[2][0][0].soc == 44
    assert mock_calc_soc.call_count == 1
    assert c.calculated_soc_state == CalculatedSocState(manual_soc=None, soc_start=42)


def test_6(monkeypatch):
    # Abgesteckt -> vom letzten Manuellen SoC hochrechnen
    # setup
    mock_calc_soc = Mock(name="calc_soc", return_value=44)
    monkeypatch.setattr(calc_soc, "calc_soc", mock_calc_soc)
    mock_value_store = Mock(name="value_store")
    monkeypatch.setattr(store, "get_car_value_store", Mock(return_value=mock_value_store))
    c = conf_vehicle_manual_from_cp()
    c.calculated_soc_state = CalculatedSocState(manual_soc=None, soc_start=42)

    # execution
    c.update(VehicleUpdateData(plug_state=True, soc_from_cp=45, timestamp_soc_from_cp=TIMESTAMP_SOC_INVALID))

    # evaluation
    assert mock_value_store.set.call_args_list[0][0][0].soc == 44
    assert mock_calc_soc.call_count == 1
    assert c.calculated_soc_state == CalculatedSocState(manual_soc=None, soc_start=42)


def test_7(monkeypatch):
    # Eintragen -> Anstecken -> Manuellen SoC hochrechnen; kein SoC von LP
    # setup
    mock_value_store = Mock(name="value_store")
    monkeypatch.setattr(store, "get_car_value_store", Mock(return_value=mock_value_store))
    c = conf_vehicle_manual()
    c.calculated_soc_state = CalculatedSocState(manual_soc=42)

    # execution
    c.update(VehicleUpdateData())
    c.update(VehicleUpdateData(plug_state=True))
    c.update(VehicleUpdateData(plug_state=True))

    # evaluation
    assert mock_value_store.set.call_args[0][0].soc == 42
    assert c.calculated_soc_state == CalculatedSocState(manual_soc=None, soc_start=42)


def test_8(monkeypatch):
    # Anstecken -> Eintragen -> Manuellen SoC hochrechnen; kein SoC von LP
    # setup
    mock_value_store = Mock(name="value_store")
    monkeypatch.setattr(store, "get_car_value_store", Mock(return_value=mock_value_store))
    c = conf_vehicle_manual()

    # execution
    c.update(VehicleUpdateData(plug_state=True))
    c.calculated_soc_state.manual_soc = 42

    c.update(VehicleUpdateData(plug_state=True))

    # evaluation
    assert mock_value_store.set.call_args[0][0].soc == 42
    assert c.calculated_soc_state == CalculatedSocState(manual_soc=None, soc_start=42)


def test_9(monkeypatch):
    # Anstecken -> aktueller SoC von EV -> SoC von Ev hochrechnen
    # setup
    mock_value_store = Mock(name="value_store")
    monkeypatch.setattr(store, "get_car_value_store", Mock(return_value=mock_value_store))
    mock_calc_soc = Mock(name="calc_soc", return_value=46)
    monkeypatch.setattr(calc_soc, "calc_soc", mock_calc_soc)
    c = conf_vehicle_api_from_cp()

    # execution
    c.update(VehicleUpdateData(plug_state=True, soc_from_cp=45, timestamp_soc_from_cp=TIMESTAMP_SOC_VALID))
    c.update(VehicleUpdateData(plug_state=True, soc_from_cp=45, timestamp_soc_from_cp=TIMESTAMP_SOC_INVALID))

    # evaluation
    assert mock_value_store.set.call_args_list[1][0][0].soc == 46
    assert mock_calc_soc.call_count == 1
    assert c.calculated_soc_state == CalculatedSocState(manual_soc=None, soc_start=45)


def test_10(monkeypatch):
    # Anstecken -> kein SoC von EV -> API
    # setup
    mock_value_store = Mock(name="value_store")
    monkeypatch.setattr(store, "get_car_value_store", Mock(return_value=mock_value_store))
    c = conf_vehicle_api()

    # execution
    c.update(VehicleUpdateData(plug_state=True))

    # evaluation
    assert mock_value_store.set.call_args_list[0][0][0].soc == 42
    assert c.calculated_soc_state == CalculatedSocState(soc_start=42)


def test_11(monkeypatch):
    # Anstecken -> kein SoC von EV -> API -> von API hochrechnen
    # setup
    mock_calc_soc = Mock(name="calc_soc", return_value=44)
    monkeypatch.setattr(calc_soc, "calc_soc", mock_calc_soc)
    mock_value_store = Mock(name="value_store")
    monkeypatch.setattr(store, "get_car_value_store", Mock(return_value=mock_value_store))
    c = conf_vehicle_api_while_charging()

    # execution
    c.update(VehicleUpdateData(plug_state=True))
    # im nächsten Zyklus wird mit calc_soc hochgerechnet
    c.update(VehicleUpdateData(plug_state=True, charge_state=True))

    # evaluation
    assert mock_value_store.set.call_args_list[1][0][0].soc == 44
    assert mock_calc_soc.call_count == 1
    assert c.calculated_soc_state == CalculatedSocState(manual_soc=None, soc_start=42)
