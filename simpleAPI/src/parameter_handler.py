"""Read/write parameter dispatch for the simpleAPI HTTP server.

Mirrors the parameter whitelist, auto-ID resolution and response-shape rules
of the HTTP dispatch layer, and reads every value straight out of the running
daemon's caches - no MQTT round-trip is made per request.
"""
from typing import Any, Callable, Dict, List, Optional, Tuple

# Write parameters, in the order they are evaluated when several are present
# in one request (the first one in this order determines the response's
# top-level success message and target-id fields).
WRITE_PARAMETER_ORDER: List[str] = [
    'set_chargemode',
    'chargecurrent',
    'minimal_pv_soc',
    'minimal_permanent_current',
    'max_price_eco',
    'chargepoint_lock',
    'bat_mode',
    'bat_power_reserve',
    'instant_charging_limit',
    'instant_charging_amount',
    'instant_charging_soc',
    'pv_charging_limit',
    'pv_charging_amount',
    'pv_charging_soc',
    'vehicle',
    'manual_soc',
    'set_io_output',
]

# bat_mode/bat_power_reserve are global settings, not chargepoint-scoped - they
# deliberately stay out of this set so they skip auto-ID resolution and leave
# chargepoint_nr null in the write response, instead of failing when no
# chargepoint is known yet.
CHARGEPOINT_WRITE_PARAMS = {
    'set_chargemode', 'chargecurrent', 'minimal_pv_soc', 'minimal_permanent_current',
    'max_price_eco', 'chargepoint_lock',
    'instant_charging_limit', 'instant_charging_amount', 'instant_charging_soc',
    'pv_charging_limit', 'pv_charging_amount', 'pv_charging_soc', 'vehicle', 'manual_soc',
}

# Full read whitelist (what counts as a recognized read parameter). Only the
# chargepoint entries and get_lastlivevaluesjson have a handler in this phase;
# the rest (counter/battery/pv/consumer/io) are recognized but return nothing
# until a later phase adds their handlers.
READ_PARAMETER_ORDER: List[str] = [
    'get_chargepoint_all',
    'get_chargepoint_voltage_p1', 'get_chargepoint_voltage_p2', 'get_chargepoint_voltage_p3',
    'get_chargepoint_voltages',
    'get_chargepoint_current_p1', 'get_chargepoint_current_p2', 'get_chargepoint_current_p3',
    'get_chargepoint_currents',
    'get_chargepoint_power', 'get_chargepoint_powers',
    'get_chargepoint_imported', 'get_chargepoint_exported',
    'get_chargepoint_daily_imported', 'get_chargepoint_daily_exported',
    'get_chargepoint_monthly_exported', 'get_chargepoint_yearly_exported',
    'get_chargepoint_frequency', 'get_chargepoint_rfid', 'get_chargepoint_rfid_timestamp',
    'get_chargepoint_evse_current',
    'get_chargepoint_power_factors',
    'get_chargepoint_power_factor_p1', 'get_chargepoint_power_factor_p2', 'get_chargepoint_power_factor_p3',
    'get_chargepoint_config_name', 'get_chargepoint_connected_vehicle_name',
    'get_chargepoint_charge_template_name', 'get_chargepoint_charge_template_min_current',
    'get_chargepoint_instant_charging_current', 'get_chargepoint_pv_charging_min_current',
    'get_chargepoint_soc', 'get_chargepoint_state_str', 'get_chargepoint_fault_str',
    'get_chargepoint_fault_state', 'get_chargepoint_phases_in_use', 'get_chargepoint_plug_state',
    'get_chargepoint_charge_state', 'get_chargepoint_chargemode',
    'get_counter',
    'get_counter_voltage_p1', 'get_counter_voltage_p2', 'get_counter_voltage_p3', 'get_counter_voltages',
    'get_counter_current_p1', 'get_counter_current_p2', 'get_counter_current_p3', 'get_counter_currents',
    'get_counter_power', 'get_counter_powers', 'get_counter_power_factors',
    'get_counter_imported', 'get_counter_exported',
    'get_counter_daily_imported', 'get_counter_daily_exported',
    'get_counter_frequency', 'get_counter_fault_str', 'get_counter_fault_state',
    'battery', 'get_battery',
    'get_battery_power', 'get_battery_soc', 'get_battery_currents',
    'get_battery_imported', 'get_battery_exported',
    'get_battery_daily_imported', 'get_battery_daily_exported',
    'get_battery_fault_str', 'get_battery_fault_state', 'get_battery_power_limit_controllable',
    'pv', 'get_pv',
    'get_pv_power', 'get_pv_currents', 'get_pv_imported', 'get_pv_exported',
    'get_pv_daily_exported', 'get_pv_monthly_exported', 'get_pv_yearly_exported',
    'get_pv_fault_str', 'get_pv_fault_state',
    'consumer', 'get_consumer', 'get_consumer_all',
    'get_consumer_power', 'get_consumer_currents', 'get_consumer_voltages', 'get_consumer_powers',
    'get_consumer_imported', 'get_consumer_exported', 'get_consumer_daily_imported',
    'get_consumer_phases_in_use', 'get_consumer_charge_state', 'get_consumer_state_str',
    'get_consumer_fault_str', 'get_consumer_fault_state', 'get_consumer_usage_type',
    'get_io_output_all', 'get_io_output',
    'get_lastlivevaluesjson',
]

COMPLEX_PARAMETERS = {
    'get_chargepoint_all', 'get_counter', 'battery', 'get_battery', 'pv', 'get_pv',
    'get_chargepoint_voltages', 'get_chargepoint_currents', 'get_chargepoint_powers',
    'get_chargepoint_power_factors',
    'get_counter_voltages', 'get_counter_currents', 'get_counter_powers', 'get_counter_power_factors',
    'get_battery_currents', 'get_pv_currents', 'get_io_output_all',
    'get_consumer_all', 'get_consumer', 'consumer',
    'get_consumer_currents', 'get_consumer_voltages', 'get_consumer_powers',
}

TYPE_PUBLIC_NAMES = {'bat': 'battery'}
SCAN_TYPES = ['chargepoint', 'bat', 'pv', 'counter', 'consumer', 'io']


def is_chargepoint_parameter(param: str) -> bool:
    return param in CHARGEPOINT_WRITE_PARAMS or 'chargepoint' in param


def is_io_parameter(param: str) -> bool:
    return param == 'set_io_output' or param.startswith('get_io_')


def get_type_from_parameter(param: str) -> str:
    if 'chargepoint' in param:
        return 'chargepoint'
    if 'io' in param:
        return 'io'
    if 'battery' in param:
        return 'bat'
    if 'pv' in param:
        return 'pv'
    if 'counter' in param:
        return 'counter'
    if 'consumer' in param:
        return 'consumer'
    return 'chargepoint'


def get_success_message(param: str, value: Any, chargepoint_id: Any) -> str:
    if param == 'set_chargemode':
        return f"Chargemode for chargepoint {chargepoint_id} set to {value}."
    if param == 'chargecurrent':
        return f"Chargecurrent for chargepoint {chargepoint_id} set to {value}A"
    if param == 'instant_charging_limit':
        return f"Instant charging limit for chargepoint {chargepoint_id} set to {value}."
    if param == 'instant_charging_amount':
        return f"Instant charging amount for chargepoint {chargepoint_id} set to {value}kWh."
    if param == 'instant_charging_soc':
        return f"Instant charging SoC for chargepoint {chargepoint_id} set to {value}%."
    if param == 'pv_charging_limit':
        return f"PV charging limit for chargepoint {chargepoint_id} set to {value}."
    if param == 'pv_charging_amount':
        return f"PV charging amount for chargepoint {chargepoint_id} set to {value}kWh."
    if param == 'pv_charging_soc':
        return f"PV charging SoC for chargepoint {chargepoint_id} set to {value}%."
    if param == 'vehicle':
        return f"Vehicle {value} assigned to chargepoint {chargepoint_id}."
    if param == 'manual_soc':
        return f"Manual SoC set to {value}% for chargepoint {chargepoint_id}."
    if param == 'set_io_output':
        return f"IO output set to {value} for io {chargepoint_id}."
    return f"Parameter {param} set to {value}."


def format_raw_output(data: Any, param_name: Optional[str] = None) -> Any:
    if isinstance(data, dict) and data:
        first_key = next(iter(data))
        first_value = data[first_key]
        if param_name == 'get_lastlivevaluesjson' and isinstance(first_value, str):
            return first_value
        if isinstance(first_value, str):
            return first_value
        if isinstance(first_value, dict) and len(first_value) == 1:
            return next(iter(first_value.values()))
        return first_value
    return data


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(default) if value is None else float(value)
    except (TypeError, ValueError):
        return float(default)


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(default) if value is None else int(value)
    except (TypeError, ValueError):
        return int(default)


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ('true', '1', 'yes', 'on')
    return bool(value)


def _as_str(value: Any, default: Any = '') -> Any:
    if value is None:
        return default
    return value if isinstance(value, str) else str(value)


def _phases(value: Any) -> List[float]:
    if not isinstance(value, (list, tuple)):
        return [0.0, 0.0, 0.0]
    return [_as_float(value[i]) if i < len(value) else 0.0 for i in range(3)]


def _is_total(id_: Any) -> bool:
    return isinstance(id_, str) and id_.strip().lower() == 'total'


def _raw(daemon: Any, topic: str) -> Any:
    return daemon.raw_value_cache.get(topic)


def _scalar(id_: Any, field: str, value: Any) -> Dict[str, Any]:
    return {f"chargepoint_{id_}": {field: value}}


def _get_chargepoint_all(daemon: Any, id_: Any) -> Dict[str, Any]:
    prefix = f"openWB/chargepoint/{id_}/get/"

    template = daemon.charge_template_cache.get(str(id_)) or {}
    chargemode_cfg = template.get('chargemode', {}) or {}
    chargemode = chargemode_cfg.get('selected', 'stop')
    instant_charging = chargemode_cfg.get('instant_charging', {}) or {}
    pv_charging = chargemode_cfg.get('pv_charging', {}) or {}
    eco_charging = chargemode_cfg.get('eco_charging', {}) or {}
    scheduled_charging = chargemode_cfg.get('scheduled_charging', {}) or {}
    instant_limit = instant_charging.get('limit', {}) or {}
    pv_limit = pv_charging.get('limit', {}) or {}

    instant_charging_current = _as_float(instant_charging.get('current', 0))
    pv_charging_min_current = _as_float(pv_charging.get('min_current', 0))

    if chargemode == 'instant_charging':
        min_current = instant_charging_current
    elif chargemode in ('pv_charging', 'eco_charging'):
        min_current = pv_charging_min_current
    elif chargemode == 'scheduled_charging':
        min_current = _as_float(scheduled_charging.get('current', 0))
    else:
        min_current = 0.0

    connected_vehicle_soc = _raw(daemon, prefix + 'connected_vehicle/soc') or {}
    connected_vehicle_info = _raw(daemon, prefix + 'connected_vehicle/info') or {}
    config = _raw(daemon, f"openWB/chargepoint/{id_}/config") or {}

    return {
        f"chargepoint_{id_}": {
            'power': _as_float(_raw(daemon, prefix + 'power')),
            'voltages': _phases(_raw(daemon, prefix + 'voltages')),
            'currents': _phases(_raw(daemon, prefix + 'currents')),
            'powers': _phases(_raw(daemon, prefix + 'powers')),
            'state_str': _as_str(_raw(daemon, prefix + 'state_str'), 'Unbekannt'),
            'fault_str': _as_str(_raw(daemon, prefix + 'fault_str'), 'Kein Fehler'),
            'fault_state': _as_int(_raw(daemon, prefix + 'fault_state')),
            'imported': _as_float(_raw(daemon, prefix + 'imported')),
            'exported': _as_float(_raw(daemon, prefix + 'exported')),
            'daily_imported': _as_float(_raw(daemon, prefix + 'daily_imported')),
            'daily_exported': _as_float(_raw(daemon, prefix + 'daily_exported')),
            'phases_in_use': _as_int(_raw(daemon, prefix + 'phases_in_use'), 1),
            'plug_state': _as_bool(_raw(daemon, prefix + 'plug_state')),
            'charge_state': _as_bool(_raw(daemon, prefix + 'charge_state')),
            'pro_soc': _as_float(_raw(daemon, prefix + 'soc')),
            'soc_timestamp': _raw(daemon, prefix + 'soc_timestamp'),
            'vehicle_id': _raw(daemon, prefix + 'vehicle_id'),
            'evse_current': _as_float(_raw(daemon, prefix + 'evse_current')),
            'frequency': _as_float(_raw(daemon, prefix + 'frequency')),
            'power_factors': _phases(_raw(daemon, prefix + 'power_factors')),
            'rfid': _as_str(_raw(daemon, prefix + 'rfid'), None),
            'rfid_timestamp': _raw(daemon, prefix + 'rfid_timestamp'),
            'config_name': config.get('name'),
            'connected_vehicle_name': connected_vehicle_info.get('name'),
            'charge_template_name': template.get('name'),
            'min_current': min_current,
            'instant_charging_current': instant_charging_current,
            'pv_charging_min_current': pv_charging_min_current,
            'instant_charging_limit': instant_limit.get('selected', 'none'),
            'instant_charging_amount': _as_int(instant_limit.get('amount', 0)),
            'instant_charging_soc': _as_int(instant_limit.get('soc', 0)),
            'pv_charging_limit': pv_limit.get('selected', 'none'),
            'pv_charging_amount': _as_int(pv_limit.get('amount', 0)),
            'pv_charging_soc': _as_int(pv_limit.get('soc', 0)),
            'max_price_eco': _as_float(eco_charging.get('max_price', 0)) * 100000,
            'soc': _as_float(connected_vehicle_soc.get('soc', 0)),
            'range_charged': _as_float(connected_vehicle_soc.get('range_charged', 0)),
            'chargemode': chargemode,
            'manual_lock': _as_bool(_raw(daemon, f"openWB/chargepoint/{id_}/set/manual_lock")),
        }
    }


def _get_chargepoint_voltage(daemon, id_, phase):
    return _scalar(id_, f'voltage_p{phase}', _phases(_raw(daemon, f"openWB/chargepoint/{id_}/get/voltages"))[phase - 1])


def _get_chargepoint_voltages(daemon, id_):
    return _scalar(id_, 'voltages', _phases(_raw(daemon, f"openWB/chargepoint/{id_}/get/voltages")))


def _get_chargepoint_current(daemon, id_, phase):
    return _scalar(id_, f'current_p{phase}', _phases(_raw(daemon, f"openWB/chargepoint/{id_}/get/currents"))[phase - 1])


def _get_chargepoint_currents(daemon, id_):
    return _scalar(id_, 'currents', _phases(_raw(daemon, f"openWB/chargepoint/{id_}/get/currents")))


def _get_chargepoint_power(daemon, id_):
    if _is_total(id_):
        return {'chargepoint_total': {'power': daemon.total_sums['chargepoint']['power']}}
    return _scalar(id_, 'power', _as_float(_raw(daemon, f"openWB/chargepoint/{id_}/get/power")))


def _get_chargepoint_powers(daemon, id_):
    return _scalar(id_, 'powers', _phases(_raw(daemon, f"openWB/chargepoint/{id_}/get/powers")))


def _get_chargepoint_imported(daemon, id_):
    if _is_total(id_):
        return {'chargepoint_total': {'imported': daemon.total_sums['chargepoint']['imported']}}
    return _scalar(id_, 'imported', _as_float(_raw(daemon, f"openWB/chargepoint/{id_}/get/imported")))


def _get_chargepoint_exported(daemon, id_):
    if _is_total(id_):
        return {'chargepoint_total': {'exported': daemon.total_sums['chargepoint']['exported']}}
    return _scalar(id_, 'exported', _as_float(_raw(daemon, f"openWB/chargepoint/{id_}/get/exported")))


def _get_chargepoint_daily_imported(daemon, id_):
    return _scalar(id_, 'daily_imported', _as_float(_raw(daemon, f"openWB/chargepoint/{id_}/get/daily_imported")))


def _get_chargepoint_daily_exported(daemon, id_):
    return _scalar(id_, 'daily_exported', _as_float(_raw(daemon, f"openWB/chargepoint/{id_}/get/daily_exported")))


def _get_chargepoint_monthly_exported(daemon, id_):
    if _is_total(id_):
        return {'chargepoint_total': {'monthly_exported': daemon.total_sums['chargepoint']['monthly_exported']}}
    return _scalar(id_, 'monthly_exported', _as_float(_raw(daemon, f"openWB/chargepoint/{id_}/get/monthly_exported")))


def _get_chargepoint_yearly_exported(daemon, id_):
    if _is_total(id_):
        return {'chargepoint_total': {'yearly_exported': daemon.total_sums['chargepoint']['yearly_exported']}}
    return _scalar(id_, 'yearly_exported', _as_float(_raw(daemon, f"openWB/chargepoint/{id_}/get/yearly_exported")))


def _get_chargepoint_frequency(daemon, id_):
    return _scalar(id_, 'frequency', _as_float(_raw(daemon, f"openWB/chargepoint/{id_}/get/frequency")))


def _get_chargepoint_rfid(daemon, id_):
    return _scalar(id_, 'rfid', _as_str(_raw(daemon, f"openWB/chargepoint/{id_}/get/rfid")))


def _get_chargepoint_rfid_timestamp(daemon, id_):
    return _scalar(id_, 'rfid_timestamp', _as_int(_raw(daemon, f"openWB/chargepoint/{id_}/get/rfid_timestamp")))


def _get_chargepoint_evse_current(daemon, id_):
    return _scalar(id_, 'evse_current', _as_float(_raw(daemon, f"openWB/chargepoint/{id_}/get/evse_current")))


def _get_chargepoint_power_factors(daemon, id_):
    return _scalar(id_, 'power_factors', _phases(_raw(daemon, f"openWB/chargepoint/{id_}/get/power_factors")))


def _get_chargepoint_power_factor(daemon, id_, phase):
    factors = _phases(_raw(daemon, f"openWB/chargepoint/{id_}/get/power_factors"))
    return _scalar(id_, f'power_factor_p{phase}', factors[phase - 1])


def _get_chargepoint_config_name(daemon, id_):
    config = _raw(daemon, f"openWB/chargepoint/{id_}/config") or {}
    return _scalar(id_, 'config_name', _as_str(config.get('name'), ''))


def _get_chargepoint_connected_vehicle_name(daemon, id_):
    info = _raw(daemon, f"openWB/chargepoint/{id_}/get/connected_vehicle/info") or {}
    return _scalar(id_, 'connected_vehicle_name', _as_str(info.get('name'), ''))


def _get_chargepoint_charge_template_name(daemon, id_):
    template = daemon.charge_template_cache.get(str(id_)) or {}
    return _scalar(id_, 'charge_template_name', _as_str(template.get('name'), ''))


def _get_chargepoint_charge_template_min_current(daemon, id_):
    template = daemon.charge_template_cache.get(str(id_)) or {}
    min_current = template.get('chargemode', {}).get('pv_charging', {}).get('min_current', 0)
    return _scalar(id_, 'charge_template_min_current', _as_float(min_current))


def _get_chargepoint_instant_charging_current(daemon, id_):
    template = daemon.charge_template_cache.get(str(id_)) or {}
    current = template.get('chargemode', {}).get('instant_charging', {}).get('current', 0)
    return _scalar(id_, 'instant_charging_current', _as_float(current))


def _get_chargepoint_pv_charging_min_current(daemon, id_):
    template = daemon.charge_template_cache.get(str(id_)) or {}
    min_current = template.get('chargemode', {}).get('pv_charging', {}).get('min_current', 0)
    return _scalar(id_, 'pv_charging_min_current', _as_float(min_current))


def _get_chargepoint_soc(daemon, id_):
    return _scalar(id_, 'soc', _as_int(_raw(daemon, f"openWB/chargepoint/{id_}/get/soc")))


def _get_chargepoint_state_str(daemon, id_):
    return _scalar(id_, 'state_str', _as_str(_raw(daemon, f"openWB/chargepoint/{id_}/get/state_str"), ''))


def _get_chargepoint_fault_str(daemon, id_):
    return _scalar(id_, 'fault_str', _as_str(_raw(daemon, f"openWB/chargepoint/{id_}/get/fault_str"), ''))


def _get_chargepoint_fault_state(daemon, id_):
    return _scalar(id_, 'fault_state', _as_int(_raw(daemon, f"openWB/chargepoint/{id_}/get/fault_state")))


def _get_chargepoint_phases_in_use(daemon, id_):
    return _scalar(id_, 'phases_in_use', _as_int(_raw(daemon, f"openWB/chargepoint/{id_}/get/phases_in_use")))


def _get_chargepoint_plug_state(daemon, id_):
    return _scalar(id_, 'plug_state', _as_bool(_raw(daemon, f"openWB/chargepoint/{id_}/get/plug_state")))


def _get_chargepoint_charge_state(daemon, id_):
    return _scalar(id_, 'charge_state', _as_bool(_raw(daemon, f"openWB/chargepoint/{id_}/get/charge_state")))


def _get_chargepoint_chargemode(daemon, id_):
    return _scalar(id_, 'chargemode', _as_str(_raw(daemon, f"openWB/chargepoint/{id_}/get/chargemode"), ''))


def _comp_scalar(component: str, id_: Any, field: str, value: Any) -> Dict[str, Any]:
    return {f"{component}_{id_}": {field: value}}


def _get_counter(daemon, id_):
    prefix = f"openWB/counter/{id_}/get/"
    return {
        f"counter_{id_}": {
            'power': _as_float(_raw(daemon, prefix + 'power')),
            'voltages': _phases(_raw(daemon, prefix + 'voltages')),
            'currents': _phases(_raw(daemon, prefix + 'currents')),
            'powers': _phases(_raw(daemon, prefix + 'powers')),
            'power_factors': _phases(_raw(daemon, prefix + 'power_factors')),
            'frequency': _as_float(_raw(daemon, prefix + 'frequency'), 50.0),
            'exported': _as_float(_raw(daemon, prefix + 'exported')),
            'daily_exported': _as_float(_raw(daemon, prefix + 'daily_exported')),
            'imported': _as_float(_raw(daemon, prefix + 'imported')),
            'daily_imported': _as_float(_raw(daemon, prefix + 'daily_imported')),
            'fault_str': _as_str(_raw(daemon, prefix + 'fault_str'), 'Kein Fehler'),
            'fault_state': _as_int(_raw(daemon, prefix + 'fault_state')),
        }
    }


def _get_counter_voltage(daemon, id_, phase):
    return _comp_scalar(
        'counter', id_, f'voltage_p{phase}', _phases(_raw(daemon, f"openWB/counter/{id_}/get/voltages"))[phase - 1])


def _get_counter_voltages(daemon, id_):
    return _comp_scalar('counter', id_, 'voltages', _phases(_raw(daemon, f"openWB/counter/{id_}/get/voltages")))


def _get_counter_current(daemon, id_, phase):
    return _comp_scalar(
        'counter', id_, f'current_p{phase}', _phases(_raw(daemon, f"openWB/counter/{id_}/get/currents"))[phase - 1])


def _get_counter_currents(daemon, id_):
    return _comp_scalar('counter', id_, 'currents', _phases(_raw(daemon, f"openWB/counter/{id_}/get/currents")))


def _get_counter_power(daemon, id_):
    return _comp_scalar('counter', id_, 'power', _as_float(_raw(daemon, f"openWB/counter/{id_}/get/power")))


def _get_counter_powers(daemon, id_):
    return _comp_scalar('counter', id_, 'powers', _phases(_raw(daemon, f"openWB/counter/{id_}/get/powers")))


def _get_counter_power_factors(daemon, id_):
    return _comp_scalar(
        'counter', id_, 'power_factors', _phases(_raw(daemon, f"openWB/counter/{id_}/get/power_factors")))


def _get_counter_imported(daemon, id_):
    return _comp_scalar('counter', id_, 'imported', _as_float(_raw(daemon, f"openWB/counter/{id_}/get/imported")))


def _get_counter_exported(daemon, id_):
    return _comp_scalar('counter', id_, 'exported', _as_float(_raw(daemon, f"openWB/counter/{id_}/get/exported")))


def _get_counter_daily_imported(daemon, id_):
    return _comp_scalar(
        'counter', id_, 'daily_imported', _as_float(_raw(daemon, f"openWB/counter/{id_}/get/daily_imported")))


def _get_counter_daily_exported(daemon, id_):
    return _comp_scalar(
        'counter', id_, 'daily_exported', _as_float(_raw(daemon, f"openWB/counter/{id_}/get/daily_exported")))


def _get_counter_frequency(daemon, id_):
    return _comp_scalar(
        'counter', id_, 'frequency', _as_float(_raw(daemon, f"openWB/counter/{id_}/get/frequency"), 50.0))


def _get_counter_fault_str(daemon, id_):
    return _comp_scalar(
        'counter', id_, 'fault_str', _as_str(_raw(daemon, f"openWB/counter/{id_}/get/fault_str"), 'Kein Fehler'))


def _get_counter_fault_state(daemon, id_):
    return _comp_scalar('counter', id_, 'fault_state', _as_int(_raw(daemon, f"openWB/counter/{id_}/get/fault_state")))


def _get_battery(daemon, id_):
    prefix = f"openWB/bat/{id_}/get/"
    return {
        f"battery_{id_}": {
            'power': _as_float(_raw(daemon, prefix + 'power')),
            'soc': _as_int(_raw(daemon, prefix + 'soc')),
            'currents': _phases(_raw(daemon, prefix + 'currents')),
            'imported': _as_float(_raw(daemon, prefix + 'imported')),
            'exported': _as_float(_raw(daemon, prefix + 'exported')),
            'daily_imported': _as_float(_raw(daemon, prefix + 'daily_imported')),
            'daily_exported': _as_float(_raw(daemon, prefix + 'daily_exported')),
            'fault_str': _as_str(_raw(daemon, prefix + 'fault_str'), 'Kein Fehler'),
            'fault_state': _as_int(_raw(daemon, prefix + 'fault_state')),
            'power_limit_controllable': _as_bool(_raw(daemon, prefix + 'power_limit_controllable')),
        }
    }


def _get_battery_power(daemon, id_):
    return _comp_scalar('battery', id_, 'power', _as_float(_raw(daemon, f"openWB/bat/{id_}/get/power")))


def _get_battery_soc(daemon, id_):
    return _comp_scalar('battery', id_, 'soc', _as_int(_raw(daemon, f"openWB/bat/{id_}/get/soc")))


def _get_battery_currents(daemon, id_):
    return _comp_scalar('battery', id_, 'currents', _phases(_raw(daemon, f"openWB/bat/{id_}/get/currents")))


def _get_battery_imported(daemon, id_):
    return _comp_scalar('battery', id_, 'imported', _as_float(_raw(daemon, f"openWB/bat/{id_}/get/imported")))


def _get_battery_exported(daemon, id_):
    return _comp_scalar('battery', id_, 'exported', _as_float(_raw(daemon, f"openWB/bat/{id_}/get/exported")))


def _get_battery_daily_imported(daemon, id_):
    return _comp_scalar(
        'battery', id_, 'daily_imported', _as_float(_raw(daemon, f"openWB/bat/{id_}/get/daily_imported")))


def _get_battery_daily_exported(daemon, id_):
    return _comp_scalar(
        'battery', id_, 'daily_exported', _as_float(_raw(daemon, f"openWB/bat/{id_}/get/daily_exported")))


def _get_battery_fault_str(daemon, id_):
    return _comp_scalar(
        'battery', id_, 'fault_str', _as_str(_raw(daemon, f"openWB/bat/{id_}/get/fault_str"), 'Kein Fehler'))


def _get_battery_fault_state(daemon, id_):
    return _comp_scalar('battery', id_, 'fault_state', _as_int(_raw(daemon, f"openWB/bat/{id_}/get/fault_state")))


def _get_battery_power_limit_controllable(daemon, id_):
    return _comp_scalar(
        'battery', id_, 'power_limit_controllable',
        _as_bool(_raw(daemon, f"openWB/bat/{id_}/get/power_limit_controllable")))


def _get_pv(daemon, id_):
    prefix = f"openWB/pv/{id_}/get/"
    return {
        f"pv_{id_}": {
            'power': _as_float(_raw(daemon, prefix + 'power')),
            'currents': _phases(_raw(daemon, prefix + 'currents')),
            'exported': _as_float(_raw(daemon, prefix + 'exported')),
            'daily_exported': _as_float(_raw(daemon, prefix + 'daily_exported')),
            'monthly_exported': _as_float(_raw(daemon, prefix + 'monthly_exported')),
            'yearly_exported': _as_float(_raw(daemon, prefix + 'yearly_exported')),
            'fault_str': _as_str(_raw(daemon, prefix + 'fault_str'), 'Kein Fehler'),
            'fault_state': _as_int(_raw(daemon, prefix + 'fault_state')),
        }
    }


def _get_pv_power(daemon, id_):
    if _is_total(id_):
        return {'pv_total': {'power': daemon.total_sums['pv']['power']}}
    return _comp_scalar('pv', id_, 'power', _as_float(_raw(daemon, f"openWB/pv/{id_}/get/power")))


def _get_pv_currents(daemon, id_):
    return _comp_scalar('pv', id_, 'currents', _phases(_raw(daemon, f"openWB/pv/{id_}/get/currents")))


def _get_pv_imported(daemon, id_):
    if _is_total(id_):
        return {'pv_total': {'imported': daemon.total_sums['pv']['imported']}}
    return _comp_scalar('pv', id_, 'imported', _as_float(_raw(daemon, f"openWB/pv/{id_}/get/imported")))


def _get_pv_exported(daemon, id_):
    if _is_total(id_):
        return {'pv_total': {'exported': daemon.total_sums['pv']['exported']}}
    return _comp_scalar('pv', id_, 'exported', _as_float(_raw(daemon, f"openWB/pv/{id_}/get/exported")))


def _get_pv_daily_exported(daemon, id_):
    return _comp_scalar('pv', id_, 'daily_exported', _as_float(_raw(daemon, f"openWB/pv/{id_}/get/daily_exported")))


def _get_pv_monthly_exported(daemon, id_):
    if _is_total(id_):
        return {'pv_total': {'monthly_exported': daemon.total_sums['pv']['monthly_exported']}}
    return _comp_scalar(
        'pv', id_, 'monthly_exported', _as_float(_raw(daemon, f"openWB/pv/{id_}/get/monthly_exported")))


def _get_pv_yearly_exported(daemon, id_):
    if _is_total(id_):
        return {'pv_total': {'yearly_exported': daemon.total_sums['pv']['yearly_exported']}}
    return _comp_scalar(
        'pv', id_, 'yearly_exported', _as_float(_raw(daemon, f"openWB/pv/{id_}/get/yearly_exported")))


def _get_pv_fault_str(daemon, id_):
    return _comp_scalar(
        'pv', id_, 'fault_str', _as_str(_raw(daemon, f"openWB/pv/{id_}/get/fault_str"), 'Kein Fehler'))


def _get_pv_fault_state(daemon, id_):
    return _comp_scalar('pv', id_, 'fault_state', _as_int(_raw(daemon, f"openWB/pv/{id_}/get/fault_state")))


def _get_consumer_all(daemon, id_):
    prefix = f"openWB/consumer/{id_}/get/"
    usage = _raw(daemon, f"openWB/consumer/{id_}/usage")
    usage_type = usage.get('type') if isinstance(usage, dict) else None
    return {
        f"consumer_{id_}": {
            'usage_type': usage_type,
            'power': _as_float(_raw(daemon, prefix + 'power')),
            'currents': _phases(_raw(daemon, prefix + 'currents')),
            'voltages': _phases(_raw(daemon, prefix + 'voltages')),
            'powers': _phases(_raw(daemon, prefix + 'powers')),
            'imported': _as_float(_raw(daemon, prefix + 'imported')),
            'exported': _as_float(_raw(daemon, prefix + 'exported')),
            'daily_imported': _as_float(_raw(daemon, prefix + 'daily_imported')),
            'phases_in_use': _as_int(_raw(daemon, prefix + 'phases_in_use')),
            'charge_state': _as_bool(_raw(daemon, prefix + 'charge_state')),
            'state_str': _as_str(_raw(daemon, prefix + 'state_str'), None),
            'fault_str': _as_str(_raw(daemon, prefix + 'fault_str'), 'Kein Fehler'),
            'fault_state': _as_int(_raw(daemon, prefix + 'fault_state')),
        }
    }


def _get_consumer_power(daemon, id_):
    return _comp_scalar('consumer', id_, 'power', _as_float(_raw(daemon, f"openWB/consumer/{id_}/get/power")))


def _get_consumer_currents(daemon, id_):
    return _comp_scalar('consumer', id_, 'currents', _phases(_raw(daemon, f"openWB/consumer/{id_}/get/currents")))


def _get_consumer_voltages(daemon, id_):
    return _comp_scalar('consumer', id_, 'voltages', _phases(_raw(daemon, f"openWB/consumer/{id_}/get/voltages")))


def _get_consumer_powers(daemon, id_):
    return _comp_scalar('consumer', id_, 'powers', _phases(_raw(daemon, f"openWB/consumer/{id_}/get/powers")))


def _get_consumer_imported(daemon, id_):
    return _comp_scalar('consumer', id_, 'imported', _as_float(_raw(daemon, f"openWB/consumer/{id_}/get/imported")))


def _get_consumer_exported(daemon, id_):
    return _comp_scalar('consumer', id_, 'exported', _as_float(_raw(daemon, f"openWB/consumer/{id_}/get/exported")))


def _get_consumer_daily_imported(daemon, id_):
    return _comp_scalar(
        'consumer', id_, 'daily_imported', _as_float(_raw(daemon, f"openWB/consumer/{id_}/get/daily_imported")))


def _get_consumer_phases_in_use(daemon, id_):
    return _comp_scalar(
        'consumer', id_, 'phases_in_use', _as_int(_raw(daemon, f"openWB/consumer/{id_}/get/phases_in_use")))


def _get_consumer_charge_state(daemon, id_):
    return _comp_scalar(
        'consumer', id_, 'charge_state', _as_bool(_raw(daemon, f"openWB/consumer/{id_}/get/charge_state")))


def _get_consumer_state_str(daemon, id_):
    return _comp_scalar(
        'consumer', id_, 'state_str', _as_str(_raw(daemon, f"openWB/consumer/{id_}/get/state_str"), None))


def _get_consumer_fault_str(daemon, id_):
    return _comp_scalar(
        'consumer', id_, 'fault_str', _as_str(_raw(daemon, f"openWB/consumer/{id_}/get/fault_str"), 'Kein Fehler'))


def _get_consumer_fault_state(daemon, id_):
    return _comp_scalar(
        'consumer', id_, 'fault_state', _as_int(_raw(daemon, f"openWB/consumer/{id_}/get/fault_state")))


def _get_consumer_usage_type(daemon, id_):
    usage = _raw(daemon, f"openWB/consumer/{id_}/usage")
    usage_type = usage.get('type') if isinstance(usage, dict) else None
    return _comp_scalar('consumer', id_, 'usage_type', usage_type)


def _get_io_output_all(daemon, id_):
    return {
        f"io_{id_}": {
            'digital_output': daemon._get_io_output_map(id_, 'digital_output'),
            'analog_output': daemon._get_io_output_map(id_, 'analog_output'),
        }
    }


def _get_io_output(daemon, id_, options):
    output_name = options.get('io_output') if options else None
    if output_name is None or str(output_name).strip() == '':
        return _get_io_output_all(daemon, id_)

    output_name = str(output_name).strip()
    output_type = daemon._normalize_io_output_type(options.get('io_output_type'))
    result = None

    if output_type == 'digital_output' or output_type is None:
        digital = daemon._get_io_output_map(id_, 'digital_output')
        if output_name in digital:
            result = digital[output_name]
            output_type = 'digital_output'

    if result is None and (output_type == 'analog_output' or output_type is None):
        analog = daemon._get_io_output_map(id_, 'analog_output')
        if output_name in analog:
            result = analog[output_name]
            output_type = 'analog_output'

    return {f"io_{id_}": {'output': output_name, 'output_type': output_type, 'value': result}}


def _get_last_live_values_json(daemon, id_=None):
    return {'get_lastlivevaluesjson': daemon.last_live_values_json}


READ_DISPATCH: Dict[str, Callable[..., Dict[str, Any]]] = {
    'get_chargepoint_all': _get_chargepoint_all,
    'get_chargepoint_voltage_p1': lambda d, i: _get_chargepoint_voltage(d, i, 1),
    'get_chargepoint_voltage_p2': lambda d, i: _get_chargepoint_voltage(d, i, 2),
    'get_chargepoint_voltage_p3': lambda d, i: _get_chargepoint_voltage(d, i, 3),
    'get_chargepoint_voltages': _get_chargepoint_voltages,
    'get_chargepoint_current_p1': lambda d, i: _get_chargepoint_current(d, i, 1),
    'get_chargepoint_current_p2': lambda d, i: _get_chargepoint_current(d, i, 2),
    'get_chargepoint_current_p3': lambda d, i: _get_chargepoint_current(d, i, 3),
    'get_chargepoint_currents': _get_chargepoint_currents,
    'get_chargepoint_power': _get_chargepoint_power,
    'get_chargepoint_powers': _get_chargepoint_powers,
    'get_chargepoint_imported': _get_chargepoint_imported,
    'get_chargepoint_exported': _get_chargepoint_exported,
    'get_chargepoint_daily_imported': _get_chargepoint_daily_imported,
    'get_chargepoint_daily_exported': _get_chargepoint_daily_exported,
    'get_chargepoint_monthly_exported': _get_chargepoint_monthly_exported,
    'get_chargepoint_yearly_exported': _get_chargepoint_yearly_exported,
    'get_chargepoint_frequency': _get_chargepoint_frequency,
    'get_chargepoint_rfid': _get_chargepoint_rfid,
    'get_chargepoint_rfid_timestamp': _get_chargepoint_rfid_timestamp,
    'get_chargepoint_evse_current': _get_chargepoint_evse_current,
    'get_chargepoint_power_factors': _get_chargepoint_power_factors,
    'get_chargepoint_power_factor_p1': lambda d, i: _get_chargepoint_power_factor(d, i, 1),
    'get_chargepoint_power_factor_p2': lambda d, i: _get_chargepoint_power_factor(d, i, 2),
    'get_chargepoint_power_factor_p3': lambda d, i: _get_chargepoint_power_factor(d, i, 3),
    'get_chargepoint_config_name': _get_chargepoint_config_name,
    'get_chargepoint_connected_vehicle_name': _get_chargepoint_connected_vehicle_name,
    'get_chargepoint_charge_template_name': _get_chargepoint_charge_template_name,
    'get_chargepoint_charge_template_min_current': _get_chargepoint_charge_template_min_current,
    'get_chargepoint_instant_charging_current': _get_chargepoint_instant_charging_current,
    'get_chargepoint_pv_charging_min_current': _get_chargepoint_pv_charging_min_current,
    'get_chargepoint_soc': _get_chargepoint_soc,
    'get_chargepoint_state_str': _get_chargepoint_state_str,
    'get_chargepoint_fault_str': _get_chargepoint_fault_str,
    'get_chargepoint_fault_state': _get_chargepoint_fault_state,
    'get_chargepoint_phases_in_use': _get_chargepoint_phases_in_use,
    'get_chargepoint_plug_state': _get_chargepoint_plug_state,
    'get_chargepoint_charge_state': _get_chargepoint_charge_state,
    'get_chargepoint_chargemode': _get_chargepoint_chargemode,
    'get_counter': _get_counter,
    'get_counter_voltage_p1': lambda d, i: _get_counter_voltage(d, i, 1),
    'get_counter_voltage_p2': lambda d, i: _get_counter_voltage(d, i, 2),
    'get_counter_voltage_p3': lambda d, i: _get_counter_voltage(d, i, 3),
    'get_counter_voltages': _get_counter_voltages,
    'get_counter_current_p1': lambda d, i: _get_counter_current(d, i, 1),
    'get_counter_current_p2': lambda d, i: _get_counter_current(d, i, 2),
    'get_counter_current_p3': lambda d, i: _get_counter_current(d, i, 3),
    'get_counter_currents': _get_counter_currents,
    'get_counter_power': _get_counter_power,
    'get_counter_powers': _get_counter_powers,
    'get_counter_power_factors': _get_counter_power_factors,
    'get_counter_imported': _get_counter_imported,
    'get_counter_exported': _get_counter_exported,
    'get_counter_daily_imported': _get_counter_daily_imported,
    'get_counter_daily_exported': _get_counter_daily_exported,
    'get_counter_frequency': _get_counter_frequency,
    'get_counter_fault_str': _get_counter_fault_str,
    'get_counter_fault_state': _get_counter_fault_state,
    'battery': _get_battery,
    'get_battery': _get_battery,
    'get_battery_power': _get_battery_power,
    'get_battery_soc': _get_battery_soc,
    'get_battery_currents': _get_battery_currents,
    'get_battery_imported': _get_battery_imported,
    'get_battery_exported': _get_battery_exported,
    'get_battery_daily_imported': _get_battery_daily_imported,
    'get_battery_daily_exported': _get_battery_daily_exported,
    'get_battery_fault_str': _get_battery_fault_str,
    'get_battery_fault_state': _get_battery_fault_state,
    'get_battery_power_limit_controllable': _get_battery_power_limit_controllable,
    'pv': _get_pv,
    'get_pv': _get_pv,
    'get_pv_power': _get_pv_power,
    'get_pv_currents': _get_pv_currents,
    'get_pv_imported': _get_pv_imported,
    'get_pv_exported': _get_pv_exported,
    'get_pv_daily_exported': _get_pv_daily_exported,
    'get_pv_monthly_exported': _get_pv_monthly_exported,
    'get_pv_yearly_exported': _get_pv_yearly_exported,
    'get_pv_fault_str': _get_pv_fault_str,
    'get_pv_fault_state': _get_pv_fault_state,
    'consumer': _get_consumer_all,
    'get_consumer': _get_consumer_all,
    'get_consumer_all': _get_consumer_all,
    'get_consumer_power': _get_consumer_power,
    'get_consumer_currents': _get_consumer_currents,
    'get_consumer_voltages': _get_consumer_voltages,
    'get_consumer_powers': _get_consumer_powers,
    'get_consumer_imported': _get_consumer_imported,
    'get_consumer_exported': _get_consumer_exported,
    'get_consumer_daily_imported': _get_consumer_daily_imported,
    'get_consumer_phases_in_use': _get_consumer_phases_in_use,
    'get_consumer_charge_state': _get_consumer_charge_state,
    'get_consumer_state_str': _get_consumer_state_str,
    'get_consumer_fault_str': _get_consumer_fault_str,
    'get_consumer_fault_state': _get_consumer_fault_state,
    'get_consumer_usage_type': _get_consumer_usage_type,
    'get_io_output_all': _get_io_output_all,
    'get_io_output': _get_io_output,
    'get_lastlivevaluesjson': _get_last_live_values_json,
}

# Read handlers that need the request's io_output/io_output_type options in
# addition to (daemon, id) - every other read handler ignores options entirely.
READ_PARAMS_WITH_OPTIONS = {'get_io_output'}

WRITE_DISPATCH: Dict[str, Callable[..., Tuple[bool, str]]] = {
    'set_chargemode': lambda d, v, i, o: d._set_chargemode(i, v),
    'chargecurrent': lambda d, v, i, o: d._set_chargecurrent(i, v),
    'minimal_pv_soc': lambda d, v, i, o: d._set_minimal_pv_soc(i, v),
    'minimal_permanent_current': lambda d, v, i, o: d._set_minimal_permanent_current(i, v),
    'max_price_eco': lambda d, v, i, o: d._set_max_price_eco(i, v),
    'chargepoint_lock': lambda d, v, i, o: d._set_chargepoint_lock(i, v),
    'bat_mode': lambda d, v, i, o: d._handle_bat_mode_operation(v),
    'bat_power_reserve': lambda d, v, i, o: d._handle_bat_power_reserve_operation(v),
    'instant_charging_limit': lambda d, v, i, o: d._handle_instant_charging_limit_operation(v, i),
    'instant_charging_amount': lambda d, v, i, o: d._handle_instant_charging_limit_amount_operation(v, i),
    'instant_charging_soc': lambda d, v, i, o: d._handle_instant_charging_limit_soc_operation(v, i),
    'pv_charging_limit': lambda d, v, i, o: d._handle_pv_charging_limit_operation(v, i),
    'pv_charging_amount': lambda d, v, i, o: d._handle_pv_charging_limit_amount_operation(v, i),
    'pv_charging_soc': lambda d, v, i, o: d._handle_pv_charging_limit_soc_operation(v, i),
    'vehicle': lambda d, v, i, o: d._set_vehicle(i, v),
    'manual_soc': lambda d, v, i, o: d._set_manual_soc(i, v),
    'set_io_output': lambda d, v, i, o: d._set_io_output(i, v, o.get('io_output'), o.get('io_output_type')),
}


def list_components(daemon: Any) -> Dict[str, List[int]]:
    return {
        TYPE_PUBLIC_NAMES.get(type_, type_): sorted(daemon.all_ids.get(type_, set()))
        for type_ in SCAN_TYPES
    }


class ParameterHandler:
    def __init__(self, daemon: Any):
        self.daemon = daemon

    def read_parameter(
            self, param: str, id_: Any, options: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        handler = READ_DISPATCH.get(param)
        if handler is None:
            return None
        if param in READ_PARAMS_WITH_OPTIONS:
            return handler(self.daemon, id_, options or {})
        return handler(self.daemon, id_)

    def write_parameter(
            self, param: str, value: Any, target_id: Any = None,
            options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        handler = WRITE_DISPATCH.get(param)
        if handler is None:
            return {'success': False, 'message': 'Unknown write parameter'}
        try:
            success, message = handler(self.daemon, value, target_id, options or {})
            return {'success': success, 'message': message}
        except Exception as exc:
            return {'success': False, 'message': str(exc)}

    def list_components(self) -> Dict[str, List[int]]:
        return list_components(self.daemon)


def extract_write_params(all_params: Dict[str, Any]) -> Dict[str, Any]:
    return {k: all_params[k] for k in WRITE_PARAMETER_ORDER if k in all_params}


def extract_read_params(all_params: Dict[str, Any]) -> Dict[str, Any]:
    return {k: all_params[k] for k in READ_PARAMETER_ORDER if k in all_params}


def dispatch_write(ph: ParameterHandler, write_params: Dict[str, Any], all_params: Dict[str, Any]) -> Dict[str, Any]:
    daemon = ph.daemon
    first_target_id = None

    for param, value in write_params.items():
        target_id = None
        id_type = None
        if is_chargepoint_parameter(param):
            target_id = all_params.get('chargepoint_nr')
            id_type = 'chargepoint'
        elif is_io_parameter(param):
            target_id = all_params.get('io_nr')
            id_type = 'io'

        if id_type is not None and target_id in (None, '', 'auto'):
            resolved = daemon.lowest_ids.get(id_type)
            if resolved is None:
                return {'success': False, 'message': f"No {id_type} devices available for auto-ID"}
            target_id = resolved

        options = {'io_output': all_params.get('io_output'), 'io_output_type': all_params.get('io_output_type')}
        result = ph.write_parameter(param, value, target_id, options)

        if first_target_id is None:
            first_target_id = target_id
        if not result['success']:
            return result

    first_param = next(iter(write_params))
    first_value = write_params[first_param]
    return {
        'success': True,
        'message': get_success_message(first_param, first_value, first_target_id),
        'data': {
            'chargepoint_nr': first_target_id if is_chargepoint_parameter(first_param) else None,
            'io_nr': first_target_id if is_io_parameter(first_param) else None,
            first_param: first_value,
        },
    }


def dispatch_read(
        ph: ParameterHandler, read_params: Dict[str, Any], all_params: Dict[str, Any],
        debug: bool) -> Tuple[Dict[str, Any], List[str]]:
    result: Dict[str, Any] = {}
    debug_info: List[str] = []

    for param, id_ in read_params.items():
        resolved_id = id_
        if param != 'get_lastlivevaluesjson' and id_ in ('auto', ''):
            type_ = get_type_from_parameter(param)
            resolved_id = ph.daemon.lowest_ids.get(type_)
            if resolved_id is None:
                if debug:
                    debug_info.append(f"Auto-ID failed for {param}: no {type_} devices known")
                if 'chargepoint' in param:
                    resolved_id = 0
                else:
                    continue

        options = {'io_output': all_params.get('io_output'), 'io_output_type': all_params.get('io_output_type')}
        data = ph.read_parameter(param, resolved_id, options)
        if data is not None:
            result.update(data)

    return result, debug_info
