from unittest.mock import Mock

import pytest

from modules.common.component_state import ConsumerState, CounterState
from modules.devices.tasmota.tasmota import bat, counter, inverter
from modules.devices.tasmota.tasmota.config import TasmotaBatSetup, TasmotaCounterSetup, TasmotaInverterSetup
from modules.devices.tasmota.tasmota.parser import TasmotaParser


METER_DATA = [
    ('ENERGY', {'Power': 230, 'Current': 1, 'Voltage': 230, 'Factor': 1, 'Total': 12.5}),
    ('Itron', {'Power': 230, 'E_in': 12.5, 'E_out': 2.5}),
    ('Itron', {'Power': 230, 'ImportActive': 12.5, 'ExportActive': 2.5}),
    ('MT681', {'Watt_summe': 230, 'Total_in': 12.5, 'Total_out': 2.5}),
    ('eBZ', {'Power': 230, 'E_in': 12.5, 'E_out': 2.5}),
    ('MT631', {'Power': 230, 'E_in': 12.5, 'E_out': 2.5}),
]
COMPONENTS = [(counter, counter.TasmotaCounter, TasmotaCounterSetup),
              (bat, bat.TasmotaBat, TasmotaBatSetup),
              (inverter, inverter.TasmotaInverter, TasmotaInverterSetup)]


def create_component(monkeypatch, component_spec, response, filtered=False):
    module, component_class, setup = component_spec
    monkeypatch.setattr(module, 'get_component_value_store', Mock(return_value=Mock()))
    monkeypatch.setattr(module, 'SimCounter', Mock(return_value=Mock(sim_count=Mock(return_value=(100, 200)))))
    peak_filter = Mock()
    peak_filter.check_values.side_effect = lambda power, imported=None, exported=None: (
        (None, None) if filtered else (imported, exported))
    monkeypatch.setattr(module, 'PeakFilter', Mock(return_value=peak_filter))
    session = Mock()
    session.get.return_value.json.return_value = response
    monkeypatch.setattr(module.req, 'get_http_session', Mock(return_value=session))
    component = component_class(setup(), device_id=0, ip_address='192.0.2.1', phase=2)
    component.initialize()
    return component


@pytest.mark.parametrize('meter_type, values', METER_DATA)
@pytest.mark.parametrize('component_spec', COMPONENTS)
def test_component_measurements(monkeypatch, component_spec, meter_type, values):
    component = create_component(monkeypatch, component_spec, {'StatusSNS': {meter_type: values}})
    component.update()
    state = component.store.set.call_args.args[0]
    assert state.power == (-230 if component_spec[0] is inverter else 230)
    assert state.exported == (200 if meter_type == 'ENERGY' else 2500)
    if component_spec[0] is not inverter:
        assert state.imported == 12500
    assert state.currents == ([0, 1, 0] if meter_type == 'ENERGY' else [0, 0, 0])
    if meter_type == 'ENERGY':
        component.sim_counter.sim_count.assert_called_once_with(state.power)
    else:
        component.sim_counter.sim_count.assert_not_called()


@pytest.mark.parametrize('component_spec', COMPONENTS)
def test_filtered_export_is_not_replaced_by_simulation(monkeypatch, component_spec):
    component = create_component(monkeypatch, component_spec,
                                 {'StatusSNS': {'MT631': {'Power': 230, 'E_in': 12.5, 'E_out': 2.5}}},
                                 filtered=True)
    component.update()
    assert component.store.set.call_args.args[0].exported is None
    component.sim_counter.sim_count.assert_not_called()


@pytest.mark.parametrize('component_spec', COMPONENTS[1:])
def test_unused_energy_fields_are_not_required(monkeypatch, component_spec):
    values = {'Power': 230, 'Current': 1}
    if component_spec[0] is bat:
        values['Total'] = 12.5
    component = create_component(monkeypatch, component_spec, {'StatusSNS': {'ENERGY': values}})
    component.update()
    assert component.store.set.call_args.args[0].currents == [0, 1, 0]


@pytest.mark.parametrize('phase', [1, 2, 3])
def test_energy_phase_assignment(phase):
    data = TasmotaParser({'StatusSNS': {'ENERGY': METER_DATA[0][1]}}, phase)
    for attribute, expected in [('currents', 1), ('voltages', 230), ('powers', 230), ('power_factors', 1)]:
        values = getattr(data, attribute)
        assert values[phase-1] == expected
        assert sum(values) == (690 if attribute == 'voltages' else expected)


@pytest.mark.parametrize('values, expected', [
    ({}, [0, 0, 0]),
    ({'36_7_0': 10}, [10, 0, 0]),
    ({'36_7_0': 10, '56_7_0': 20, '76_7_0': 30}, [10, 20, 30]),
])
def test_ebz_phase_powers(values, expected):
    assert TasmotaParser({'StatusSNS': {'eBZ': values}}).powers == expected


def test_inverter_does_not_require_import_value(monkeypatch):
    component = create_component(monkeypatch, COMPONENTS[2],
                                 {'StatusSNS': {'MT681': {'Watt_summe': 230, 'Total_out': 2.5}}})
    component.update()
    assert component.store.set.call_args.args[0].exported == 2500


def test_power_only_status_zero():
    data = TasmotaParser({'Status': {'Power': 1}, 'StatusSNS': {'ENERGY': {'Power': 230}}})
    assert data.power == 230


def test_unsupported_meter():
    with pytest.raises(ValueError, match='Nicht unterstützter Tasmota Zählertyp'):
        TasmotaParser({'StatusSNS': {'unknown': {}}})


@pytest.mark.parametrize('meter_type', ['ENERGY', 'Itron', 'MT681', 'eBZ', 'MT631'])
@pytest.mark.parametrize('attribute', [
    'power', 'imported', 'exported', 'currents', 'voltages', 'powers', 'power_factors',
])
def test_missing_measurements_use_counter_state_defaults(meter_type, attribute):
    data = TasmotaParser({'StatusSNS': {meter_type: {}}})
    assert getattr(data, attribute) == getattr(CounterState(), attribute)


def test_default_lists_are_independent():
    data = TasmotaParser({'StatusSNS': {'MT631': {}}})
    values = data.voltages
    values[0] = 0
    assert data.voltages == CounterState().voltages


def test_missing_phase_measurements_use_counter_state_defaults():
    data = TasmotaParser({'StatusSNS': {'ENERGY': {'Voltage': 240}}}, phase=2)
    expected = CounterState().voltages
    expected[1] = 240
    assert data.voltages == expected


@pytest.mark.parametrize('power, expected', [(0, False), (1, True)])
@pytest.mark.parametrize('status_sns', [None, {}, {'ENERGY': {'Power': 230}}])
def test_relay_state(power, expected, status_sns):
    response = {'Status': {'Power': power}}
    if status_sns is not None:
        response['StatusSNS'] = status_sns
    data = TasmotaParser(response)
    assert data.state is expected
    assert data.power == (230 if status_sns and 'ENERGY' in status_sns else CounterState().power)


def test_missing_relay_state_uses_consumer_state_default():
    data = TasmotaParser({'StatusSNS': {'ENERGY': {'Power': 230}}})
    assert data.state == ConsumerState().state
