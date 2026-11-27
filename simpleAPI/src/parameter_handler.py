"""Read/write parameter dispatch for the simpleAPI HTTP server.

Mirrors the parameter whitelist, auto-ID resolution and response-shape rules
of the HTTP dispatch layer, and reads every value straight out of the running
daemon's caches - no MQTT round-trip is made per request.
"""
import math
import re
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

# Full read whitelist (what counts as a recognized read parameter).
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
    'get_chargepoint_soc', 'get_chargepoint_state_str', 'get_chargepoint_limit', 'get_chargepoint_fault_str',
    'get_chargepoint_fault_state', 'get_chargepoint_phases_in_use', 'get_chargepoint_plug_state',
    'get_chargepoint_charge_state', 'get_chargepoint_chargemode',
    'get_counter',
    'get_counter_voltage_p1', 'get_counter_voltage_p2', 'get_counter_voltage_p3', 'get_counter_voltages',
    'get_counter_current_p1', 'get_counter_current_p2', 'get_counter_current_p3', 'get_counter_currents',
    'get_counter_power', 'get_counter_powers', 'get_counter_power_factors',
    'get_counter_imported', 'get_counter_exported',
    'get_counter_daily_imported', 'get_counter_daily_exported',
    'get_counter_frequency', 'get_counter_fault_str', 'get_counter_fault_state', 'get_counter_local_power',
    'battery', 'get_battery',
    'get_battery_power', 'get_battery_soc', 'get_battery_currents',
    'get_battery_imported', 'get_battery_exported',
    'get_battery_daily_imported', 'get_battery_daily_exported',
    'get_battery_fault_str', 'get_battery_fault_state', 'get_battery_power_limit_controllable',
    'get_battery_state_str', 'get_battery_max_charge_power', 'get_battery_max_discharge_power',
    'pv', 'get_pv',
    'get_pv_power', 'get_pv_currents', 'get_pv_imported', 'get_pv_exported',
    'get_pv_daily_exported', 'get_pv_monthly_exported', 'get_pv_yearly_exported',
    'get_pv_fault_str', 'get_pv_fault_state',
    'consumer', 'get_consumer', 'get_consumer_all',
    'get_consumer_power', 'get_consumer_currents', 'get_consumer_voltages', 'get_consumer_powers',
    'get_consumer_imported', 'get_consumer_exported', 'get_consumer_daily_imported',
    'get_consumer_phases_in_use', 'get_consumer_charge_state', 'get_consumer_state_str',
    'get_consumer_fault_str', 'get_consumer_fault_state', 'get_consumer_usage_type',
    'get_consumer_temperatures', 'get_consumer_set_power', 'get_consumer_state', 'get_consumer_plug_state',
    'get_consumer_rfid', 'get_consumer_rfid_timestamp',
    'get_home_consumption',
    'get_io_output_all', 'get_io_output', 'get_io_input_all',
    'get_lastlivevaluesjson',
]

COMPLEX_PARAMETERS = {
    'get_chargepoint_all', 'get_counter', 'battery', 'get_battery', 'pv', 'get_pv',
    'get_chargepoint_voltages', 'get_chargepoint_currents', 'get_chargepoint_powers',
    'get_chargepoint_power_factors',
    'get_counter_voltages', 'get_counter_currents', 'get_counter_powers', 'get_counter_power_factors',
    'get_battery_currents', 'get_pv_currents', 'get_io_output_all', 'get_io_input_all',
    'get_chargepoint_limit',
    'get_consumer_all', 'get_consumer', 'consumer',
    'get_consumer_currents', 'get_consumer_voltages', 'get_consumer_powers', 'get_consumer_temperatures',
    'get_home_consumption',
}

# Not tied to a component ID - the ID in the request is ignored.
GLOBAL_READ_PARAMETERS = {'get_home_consumption', 'get_lastlivevaluesjson'}

TYPE_PUBLIC_NAMES = {'bat': 'battery'}
SCAN_TYPES = ['chargepoint', 'bat', 'pv', 'counter', 'consumer', 'io']


def is_chargepoint_parameter(param: str) -> bool:
    return param in CHARGEPOINT_WRITE_PARAMS or 'chargepoint' in param


def is_io_parameter(param: str) -> bool:
    return param == 'set_io_output' or param.startswith('get_io_')


def get_type_from_parameter(param: str) -> str:
    if 'chargepoint' in param:
        return 'chargepoint'
    if param == 'get_io_input_all':
        return 'io_input'
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


def php_echo(value: Any) -> str:
    """What PHP's echo prints (precision=14 for floats, true -> "1", false/null -> "")."""
    if value is None:
        return ''
    if isinstance(value, bool):
        return '1' if value else ''
    if isinstance(value, float):
        if value != value:
            return 'NAN'
        if value in (math.inf, -math.inf):
            return 'INF' if value > 0 else '-INF'
        text = f"{value:.14G}"
        if 'E' in text:
            mantissa, exponent = text.split('E')
            if '.' not in mantissa:
                mantissa += '.0'
            text = f"{mantissa}E{exponent[0]}{int(exponent[1:])}"
        return text
    if isinstance(value, (dict, list)):
        return 'Array'
    return str(value)


def format_raw_output(data: Any, param_name: Optional[str] = None) -> Any:
    if isinstance(data, dict) and not data:
        return ''
    if isinstance(data, dict):
        first_key = next(iter(data))
        first_value = data[first_key]
        if isinstance(first_value, str):
            return first_value
        if isinstance(first_value, dict) and len(first_value) == 1:
            return next(iter(first_value.values()))
        return first_value
    return data


def _as_float(value: Any, default: float = 0.0) -> float:
    try:
        number = float(default) if value is None else float(value)
    except (TypeError, ValueError):
        return float(default)
    # PHP's floatval() never produced NaN/INF, and they are not valid JSON
    return number if math.isfinite(number) else float(default)


def _as_int(value: Any, default: int = 0) -> int:
    try:
        return int(default) if value is None else int(value)
    except (TypeError, ValueError):
        return int(default)


def _as_bool(value: Any, default: Any = None) -> bool:
    # default is unused (bool has no sensible "missing" distinct from False) -
    # accepted only so this coercer has the same (value, default) signature as
    # the others and can sit in the same dispatch table.
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in ('true', '1', 'yes', 'on')
    return bool(value)


def _opt_float(value: Any, default: Any = None) -> Optional[float]:
    # missing/invalid stays null - for values where 0 would be a misleading default
    try:
        number = default if value is None else float(value)
    except (TypeError, ValueError):
        return default
    return number if number is None or math.isfinite(number) else default


def _float_list(value: Any, default: Any = None) -> List[Optional[float]]:
    if not isinstance(value, (list, tuple)):
        return []
    return [_opt_float(item) for item in value]


def _as_str(value: Any, default: Any = '') -> Any:
    if value is None:
        return default
    return value if isinstance(value, str) else str(value)


def _phases(value: Any, default: Any = None) -> List[float]:
    # default is unused (each slot already defaults to 0.0) - accepted only for
    # a uniform (value, default) coercer signature, see _as_bool.
    if not isinstance(value, (list, tuple)):
        return [0.0, 0.0, 0.0]
    return [_as_float(value[i]) if i < len(value) else 0.0 for i in range(3)]


def _is_total(id_: Any) -> bool:
    return isinstance(id_, str) and id_.strip().lower() == 'total'


def _raw(daemon: Any, topic: str) -> Any:
    return daemon.raw_value_cache.get(topic)


def _comp_scalar(component: str, id_: Any, field: str, value: Any) -> Dict[str, Any]:
    return {f"{component}_{id_}": {field: value}}


def _parse_limit(value: Any) -> Dict[str, Any]:
    # control_parameter/limit: why the charge power is currently limited (e.g. §14a dimming, load management,
    # counter fuse). Both fields are null when no limit is active.
    limit = value if isinstance(value, dict) else {}
    return {'message': limit.get('message'), 'limiting_value': limit.get('limiting_value')}


def _max_price_eco(max_price: Any) -> float:
    # PHP rounded the stored EUR/Wh price to 6 decimals before converting it to ct/kWh
    return float(f"{_as_float(max_price):.6f}") * 100000


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
            'limit': _parse_limit(_raw(daemon, f"openWB/chargepoint/{id_}/control_parameter/limit")),
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
            'minimal_pv_soc': _as_int(pv_charging.get('min_soc', 0)),
            'max_price_eco': _max_price_eco(eco_charging.get('max_price')),
            'soc': _as_float(connected_vehicle_soc.get('soc', 0)),
            'range_charged': _as_float(connected_vehicle_soc.get('range_charged', 0)),
            'chargemode': chargemode,
            'manual_lock': _as_bool(_raw(daemon, f"openWB/chargepoint/{id_}/set/manual_lock")),
        }
    }


def _make_scalar_handler(
        component: str, mqtt_component: str, suffix: str, field: str,
        coercer: Callable[[Any, Any], Any], default: Any, total_aware: bool) -> Callable[[Any, Any], Dict[str, Any]]:
    """Build a read handler for the common "look up one get/<suffix> topic, coerce
    it, wrap it as {component_id: {field: value}}" shape - optionally serving
    id="total" from daemon.total_sums instead, for the handful of metrics that are
    continuously aggregated across all known IDs of a component type."""
    def handler(daemon: Any, id_: Any) -> Dict[str, Any]:
        if total_aware and _is_total(id_):
            record = getattr(daemon, 'record_total', None)
            if record:
                record(mqtt_component, field)
            return {f"{component}_total": {field: daemon.total_sums[mqtt_component][field]}}
        if (component, suffix) in _NOTHING_WITHOUT_TOPIC and not _has_topic(
                daemon, f"openWB/{mqtt_component}/{id_}/get/{suffix}"):
            return {}
        raw = _raw(daemon, f"openWB/{mqtt_component}/{id_}/get/{suffix}")
        return _comp_scalar(component, id_, field, coercer(raw, default))
    return handler


# Scalar read-parameter table: one row per `get_<component>_<field>` handler that
# reduces to "read openWB/<mqtt_component>/<id>/get/<suffix>, coerce, wrap".
# total_aware marks the metrics that are also continuously aggregated across all
# known IDs and so additionally serve id="total" from daemon.total_sums.
#
# (component, mqtt_component, topic_suffix, field, coercer, default, total_aware)
SCALAR_READ_TABLE: List[Tuple[str, str, str, str, Callable[[Any, Any], Any], Any, bool]] = [
    # chargepoint
    ('chargepoint', 'chargepoint', 'power', 'power', _as_float, 0.0, True),
    ('chargepoint', 'chargepoint', 'powers', 'powers', _phases, None, False),
    ('chargepoint', 'chargepoint', 'imported', 'imported', _as_float, 0.0, True),
    ('chargepoint', 'chargepoint', 'exported', 'exported', _as_float, 0.0, True),
    ('chargepoint', 'chargepoint', 'daily_imported', 'daily_imported', _as_float, 0.0, False),
    ('chargepoint', 'chargepoint', 'daily_exported', 'daily_exported', _as_float, 0.0, False),
    ('chargepoint', 'chargepoint', 'monthly_exported', 'monthly_exported', _as_float, 0.0, True),
    ('chargepoint', 'chargepoint', 'yearly_exported', 'yearly_exported', _as_float, 0.0, True),
    ('chargepoint', 'chargepoint', 'frequency', 'frequency', _as_float, 0.0, False),
    ('chargepoint', 'chargepoint', 'rfid', 'rfid', _as_str, '', False),
    ('chargepoint', 'chargepoint', 'rfid_timestamp', 'rfid_timestamp', _as_int, 0, False),
    ('chargepoint', 'chargepoint', 'evse_current', 'evse_current', _as_float, 0.0, False),
    ('chargepoint', 'chargepoint', 'soc', 'soc', _as_int, 0, False),
    ('chargepoint', 'chargepoint', 'state_str', 'state_str', _as_str, '', False),
    ('chargepoint', 'chargepoint', 'fault_str', 'fault_str', _as_str, '', False),
    ('chargepoint', 'chargepoint', 'fault_state', 'fault_state', _as_int, 0, False),
    ('chargepoint', 'chargepoint', 'phases_in_use', 'phases_in_use', _as_int, 0, False),
    ('chargepoint', 'chargepoint', 'plug_state', 'plug_state', _as_bool, None, False),
    ('chargepoint', 'chargepoint', 'charge_state', 'charge_state', _as_bool, None, False),
    ('chargepoint', 'chargepoint', 'chargemode', 'chargemode', _as_str, '', False),
    # counter
    ('counter', 'counter', 'power', 'power', _as_float, 0.0, False),
    ('counter', 'counter', 'powers', 'powers', _phases, None, False),
    ('counter', 'counter', 'power_factors', 'power_factors', _phases, None, False),
    ('counter', 'counter', 'imported', 'imported', _as_float, 0.0, False),
    ('counter', 'counter', 'exported', 'exported', _as_float, 0.0, False),
    ('counter', 'counter', 'daily_imported', 'daily_imported', _as_float, 0.0, False),
    ('counter', 'counter', 'daily_exported', 'daily_exported', _as_float, 0.0, False),
    ('counter', 'counter', 'frequency', 'frequency', _as_float, 50.0, False),
    ('counter', 'counter', 'fault_str', 'fault_str', _as_str, 'Kein Fehler', False),
    ('counter', 'counter', 'fault_state', 'fault_state', _as_int, 0, False),
    ('counter', 'counter', 'local_power', 'local_power', _as_float, 0.0, False),
    # battery (mqtt topic path is "bat", output/field prefix is "battery")
    ('battery', 'bat', 'power', 'power', _as_float, 0.0, False),
    ('battery', 'bat', 'soc', 'soc', _as_int, 0, False),
    ('battery', 'bat', 'currents', 'currents', _phases, None, False),
    ('battery', 'bat', 'imported', 'imported', _as_float, 0.0, False),
    ('battery', 'bat', 'exported', 'exported', _as_float, 0.0, False),
    ('battery', 'bat', 'daily_imported', 'daily_imported', _as_float, 0.0, False),
    ('battery', 'bat', 'daily_exported', 'daily_exported', _as_float, 0.0, False),
    ('battery', 'bat', 'fault_str', 'fault_str', _as_str, 'Kein Fehler', False),
    ('battery', 'bat', 'fault_state', 'fault_state', _as_int, 0, False),
    ('battery', 'bat', 'power_limit_controllable', 'power_limit_controllable', _as_bool, None, False),
    ('battery', 'bat', 'state_str', 'state_str', _as_str, '', False),
    ('battery', 'bat', 'max_charge_power', 'max_charge_power', _as_float, 0.0, False),
    ('battery', 'bat', 'max_discharge_power', 'max_discharge_power', _as_float, 0.0, False),
    # pv
    ('pv', 'pv', 'power', 'power', _as_float, 0.0, True),
    ('pv', 'pv', 'currents', 'currents', _phases, None, False),
    ('pv', 'pv', 'imported', 'imported', _as_float, 0.0, True),
    ('pv', 'pv', 'exported', 'exported', _as_float, 0.0, True),
    ('pv', 'pv', 'daily_exported', 'daily_exported', _as_float, 0.0, False),
    ('pv', 'pv', 'monthly_exported', 'monthly_exported', _as_float, 0.0, True),
    ('pv', 'pv', 'yearly_exported', 'yearly_exported', _as_float, 0.0, True),
    ('pv', 'pv', 'fault_str', 'fault_str', _as_str, 'Kein Fehler', False),
    ('pv', 'pv', 'fault_state', 'fault_state', _as_int, 0, False),
    # consumer
    ('consumer', 'consumer', 'power', 'power', _as_float, 0.0, False),
    ('consumer', 'consumer', 'currents', 'currents', _phases, None, False),
    ('consumer', 'consumer', 'voltages', 'voltages', _phases, None, False),
    ('consumer', 'consumer', 'powers', 'powers', _phases, None, False),
    ('consumer', 'consumer', 'imported', 'imported', _as_float, 0.0, False),
    ('consumer', 'consumer', 'exported', 'exported', _as_float, 0.0, False),
    ('consumer', 'consumer', 'daily_imported', 'daily_imported', _as_float, 0.0, False),
    ('consumer', 'consumer', 'phases_in_use', 'phases_in_use', _as_int, 0, False),
    ('consumer', 'consumer', 'charge_state', 'charge_state', _as_bool, None, False),
    ('consumer', 'consumer', 'state_str', 'state_str', _as_str, None, False),
    ('consumer', 'consumer', 'fault_str', 'fault_str', _as_str, 'Kein Fehler', False),
    ('consumer', 'consumer', 'fault_state', 'fault_state', _as_int, 0, False),
    ('consumer', 'consumer', 'temperatures', 'temperatures', _float_list, None, False),
    ('consumer', 'consumer', 'set_power', 'set_power', _opt_float, None, False),
    ('consumer', 'consumer', 'state', 'state', _as_bool, None, False),
    ('consumer', 'consumer', 'plug_state', 'plug_state', _as_bool, None, False),
    ('consumer', 'consumer', 'rfid', 'rfid', _as_str, '', False),
    ('consumer', 'consumer', 'rfid_timestamp', 'rfid_timestamp', _as_int, 0, False),
]


# PHP answered the array reads of chargepoints (voltages, currents, powers) with nothing when the topic does not exist,
# every other read with zeros
_NOTHING_WITHOUT_TOPIC = {('chargepoint', 'voltages'), ('chargepoint', 'currents'), ('chargepoint', 'powers')}
_MISSING = object()


def _has_topic(daemon: Any, topic: str) -> bool:
    return daemon.raw_value_cache.get(topic, _MISSING) is not _MISSING


def _make_phase_handlers(component: str, mqtt_component: str, suffix: str) -> Dict[str, Callable[..., Any]]:
    """Build the 4 read handlers (plural array + 3 per-phase scalars) that share
    one underlying openWB/<mqtt_component>/<id>/get/<suffix> topic, e.g. suffix
    "voltages" yields get_<component>_voltages plus _voltage_p1/_p2/_p3."""
    singular = suffix[:-1]  # 'voltages' -> 'voltage', 'power_factors' -> 'power_factor'

    def topic(id_: Any) -> str:
        return f"openWB/{mqtt_component}/{id_}/get/{suffix}"

    nothing = (component, suffix) in _NOTHING_WITHOUT_TOPIC

    def plural_handler(daemon: Any, id_: Any) -> Optional[Dict[str, Any]]:
        if nothing and not _has_topic(daemon, topic(id_)):
            return None
        return _comp_scalar(component, id_, suffix, _phases(_raw(daemon, topic(id_))))

    def make_phase_handler(phase: int) -> Callable[[Any, Any], Optional[Dict[str, Any]]]:
        def handler(daemon: Any, id_: Any) -> Optional[Dict[str, Any]]:
            if nothing and not _has_topic(daemon, topic(id_)):
                return None
            values = _phases(_raw(daemon, topic(id_)))
            return _comp_scalar(component, id_, f"{singular}_p{phase}", values[phase - 1])
        return handler

    handlers: Dict[str, Callable[..., Any]] = {f"get_{component}_{suffix}": plural_handler}
    for phase in (1, 2, 3):
        handlers[f"get_{component}_{singular}_p{phase}"] = make_phase_handler(phase)
    return handlers


# (component, mqtt_component, topic_suffix) for the phase-indexed getters that
# have both a plural array endpoint and 3 individual per-phase endpoints.
PHASE_READ_TABLE: List[Tuple[str, str, str]] = [
    ('chargepoint', 'chargepoint', 'voltages'),
    ('chargepoint', 'chargepoint', 'currents'),
    ('chargepoint', 'chargepoint', 'power_factors'),
    ('counter', 'counter', 'voltages'),
    ('counter', 'counter', 'currents'),
]


def _get_chargepoint_config_name(daemon, id_):
    config = _raw(daemon, f"openWB/chargepoint/{id_}/config") or {}
    return _comp_scalar('chargepoint', id_, 'config_name', _as_str(config.get('name'), ''))


def _get_chargepoint_connected_vehicle_name(daemon, id_):
    info = _raw(daemon, f"openWB/chargepoint/{id_}/get/connected_vehicle/info") or {}
    return _comp_scalar('chargepoint', id_, 'connected_vehicle_name', _as_str(info.get('name'), ''))


def _get_chargepoint_charge_template_name(daemon, id_):
    template = daemon.charge_template_cache.get(str(id_)) or {}
    return _comp_scalar('chargepoint', id_, 'charge_template_name', _as_str(template.get('name'), ''))


def _get_chargepoint_charge_template_min_current(daemon, id_):
    template = daemon.charge_template_cache.get(str(id_)) or {}
    min_current = template.get('chargemode', {}).get('pv_charging', {}).get('min_current', 0)
    return _comp_scalar('chargepoint', id_, 'charge_template_min_current', _as_float(min_current))


def _get_chargepoint_instant_charging_current(daemon, id_):
    template = daemon.charge_template_cache.get(str(id_)) or {}
    current = template.get('chargemode', {}).get('instant_charging', {}).get('current', 0)
    return _comp_scalar('chargepoint', id_, 'instant_charging_current', _as_float(current))


def _get_chargepoint_pv_charging_min_current(daemon, id_):
    template = daemon.charge_template_cache.get(str(id_)) or {}
    min_current = template.get('chargemode', {}).get('pv_charging', {}).get('min_current', 0)
    return _comp_scalar('chargepoint', id_, 'pv_charging_min_current', _as_float(min_current))


def _get_chargepoint_limit(daemon, id_):
    limit = _raw(daemon, f"openWB/chargepoint/{id_}/control_parameter/limit")
    return _comp_scalar('chargepoint', id_, 'limit', _parse_limit(limit))


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
            'local_power': _as_float(_raw(daemon, prefix + 'local_power')),
            'exported': _as_float(_raw(daemon, prefix + 'exported')),
            'daily_exported': _as_float(_raw(daemon, prefix + 'daily_exported')),
            'imported': _as_float(_raw(daemon, prefix + 'imported')),
            'daily_imported': _as_float(_raw(daemon, prefix + 'daily_imported')),
            'fault_str': _as_str(_raw(daemon, prefix + 'fault_str'), 'Kein Fehler'),
            'fault_state': _as_int(_raw(daemon, prefix + 'fault_state')),
        }
    }


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
            'state_str': _as_str(_raw(daemon, prefix + 'state_str'), ''),
            'max_charge_power': _as_float(_raw(daemon, prefix + 'max_charge_power')),
            'max_discharge_power': _as_float(_raw(daemon, prefix + 'max_discharge_power')),
        }
    }


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
            'plug_state': _as_bool(_raw(daemon, prefix + 'plug_state')),
            'set_power': _opt_float(_raw(daemon, prefix + 'set_power')),
            'state': _as_bool(_raw(daemon, prefix + 'state')),
            'temperatures': _float_list(_raw(daemon, prefix + 'temperatures')),
            'rfid': _as_str(_raw(daemon, prefix + 'rfid'), None),
            'rfid_timestamp': _raw(daemon, prefix + 'rfid_timestamp'),
            'fault_str': _as_str(_raw(daemon, prefix + 'fault_str'), 'Kein Fehler'),
            'fault_state': _as_int(_raw(daemon, prefix + 'fault_state')),
        }
    }


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


def _get_home_consumption(daemon, id_):
    return {
        'home_consumption': {
            'power': _as_float(_raw(daemon, 'openWB/counter/set/home_consumption')),
            'daily_imported': _as_float(_raw(daemon, 'openWB/counter/set/daily_yield_home_consumption')),
            'imported': _as_float(_raw(daemon, 'openWB/counter/set/imported_home_consumption')),
        }
    }


def _get_lastlivevaluesjson(daemon, id_):
    value = _raw(daemon, 'openWB/graph/lastlivevaluesJson')
    return {'get_lastlivevaluesjson': value}


def _get_io_input_all(daemon, id_):
    return {
        f"io_{id_}": {
            'digital_input': daemon._get_io_output_map(id_, 'digital_input'),
            'analog_input': daemon._get_io_output_map(id_, 'analog_input'),
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


def _build_scalar_read_dispatch() -> Dict[str, Callable[..., Dict[str, Any]]]:
    dispatch: Dict[str, Callable[..., Dict[str, Any]]] = {}
    for component, mqtt_component, suffix, field, coercer, default, total_aware in SCALAR_READ_TABLE:
        dispatch[f"get_{component}_{field}"] = _make_scalar_handler(
            component, mqtt_component, suffix, field, coercer, default, total_aware)
    for component, mqtt_component, suffix in PHASE_READ_TABLE:
        dispatch.update(_make_phase_handlers(component, mqtt_component, suffix))
    return dispatch


READ_DISPATCH: Dict[str, Callable[..., Dict[str, Any]]] = {
    'get_chargepoint_all': _get_chargepoint_all,
    **_build_scalar_read_dispatch(),
    'get_chargepoint_limit': _get_chargepoint_limit,
    'get_chargepoint_config_name': _get_chargepoint_config_name,
    'get_chargepoint_connected_vehicle_name': _get_chargepoint_connected_vehicle_name,
    'get_chargepoint_charge_template_name': _get_chargepoint_charge_template_name,
    'get_chargepoint_charge_template_min_current': _get_chargepoint_charge_template_min_current,
    'get_chargepoint_instant_charging_current': _get_chargepoint_instant_charging_current,
    'get_chargepoint_pv_charging_min_current': _get_chargepoint_pv_charging_min_current,
    'get_counter': _get_counter,
    'battery': _get_battery,
    'get_battery': _get_battery,
    'pv': _get_pv,
    'get_pv': _get_pv,
    'consumer': _get_consumer_all,
    'get_consumer': _get_consumer_all,
    'get_consumer_all': _get_consumer_all,
    'get_consumer_usage_type': _get_consumer_usage_type,
    'get_io_output_all': _get_io_output_all,
    'get_io_output': _get_io_output,
    'get_io_input_all': _get_io_input_all,
    'get_home_consumption': _get_home_consumption,
    'get_lastlivevaluesjson': _get_lastlivevaluesjson,
}

# Read handlers that need the request's io_output/io_output_type options in
# addition to (daemon, id) - every other read handler ignores options entirely.
READ_PARAMS_WITH_OPTIONS = {'get_io_output'}

# The HTTP write parameters keep the value contract of the PHP API: PHP's floatval()/intval() parsing and the
# PHP error texts. The MQTT set topics keep their own, stricter handlers in the daemon.
_NUMBER_PREFIX = re.compile(r'\s*[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?')
_INT_MAX = 2 ** 63 - 1


_NUMBER = re.compile(r'\s*[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?\s*')


def is_numeric(value: Any) -> bool:
    """Whole value is a number. PHP's floatval()/intval() turned anything else into 0 or a prefix; that is
    rejected here (documented in COMPATIBILITY.md)."""
    return _NUMBER.fullmatch(str(value)) is not None


def php_floatval(value: Any) -> float:
    match = _NUMBER_PREFIX.match(str(value))
    return float(match.group()) if match else 0.0


def php_intval(value: Any) -> int:
    number = php_floatval(value)
    if number != number:
        return 0
    return max(-_INT_MAX - 1, min(_INT_MAX, int(number)))


def _whole_as_int(number: float) -> Any:
    """A whole number is published as an integer (`10`, not `10.0`), like the PHP API did."""
    return int(number) if number == int(number) and abs(number) < 1e15 else number


def _template_topic(chargepoint_id: Any) -> str:
    return f"openWB/set/chargepoint/{chargepoint_id}/set/charge_template"


def _write_template(daemon, chargepoint_id, mode_key: Optional[str], keypath: Tuple[str, ...], value: Any,
                    error_prefix: str) -> Tuple[bool, str]:
    """Set keypath in the charge_template of a chargepoint, like the PHP read-modify-write on the template.
    mode_key is the chargemode section the template must contain (None: it is created)."""
    template = daemon._get_charge_template(chargepoint_id)
    if template is None:
        return False, (f"{error_prefix}No data received for topic: "
                       f"openWB/chargepoint/{chargepoint_id}/set/charge_template")
    chargemode = template.get('chargemode')
    if mode_key is None:
        if chargemode is None:
            template['chargemode'] = {}
    elif not template or not isinstance(chargemode, dict) or chargemode.get(mode_key) is None:
        return False, f"Invalid charge template format or missing {mode_key}"
    container = template
    for step in keypath[:-1]:
        if not isinstance(container.get(step), dict):
            container[step] = {}
        container = container[step]
    container[keypath[-1]] = value
    daemon._publish_json(_template_topic(chargepoint_id), template)
    return True, ''


_CHARGEMODES = {
    'instant': 'instant_charging', 'pv': 'pv_charging', 'eco': 'eco_charging', 'stop': 'stop',
    'target': 'scheduled_charging', 'instant_charging': 'instant_charging', 'pv_charging': 'pv_charging',
    'eco_charging': 'eco_charging', 'scheduled_charging': 'scheduled_charging',
}


def _http_set_chargemode(d, value, chargepoint_id, options):
    if value not in _CHARGEMODES:
        return False, 'Invalid chargemode. Valid modes: ' + ', '.join(_CHARGEMODES)
    return _write_template(d, chargepoint_id, None, ('chargemode', 'selected'), _CHARGEMODES[value],
                           'Error setting chargemode: ')


def _http_template_number(mode_key: str, keypath: Tuple[str, ...], parse: Callable[[Any], Any], label: str,
                          error_prefix: str):
    def handler(d, value, chargepoint_id, options):
        if not is_numeric(value):
            return False, f"Invalid {label} value: {value}"
        return _write_template(d, chargepoint_id, mode_key, keypath, _whole_as_int(parse(value)), error_prefix)
    return handler


def _http_max_price_eco(d, value, chargepoint_id, options):
    if not is_numeric(value):
        return False, f"Invalid price value: {value}"
    return _write_template(d, chargepoint_id, 'eco_charging', ('chargemode', 'eco_charging', 'max_price'),
                           php_floatval(value) / 100000, 'Error setting max price eco: ')


LIMIT_LABELS = {'instant_charging': 'instant charging', 'pv_charging': 'PV charging'}


def _http_limit(mode_key: str):
    def handler(d, value, chargepoint_id, options):
        if value not in ('none', 'amount', 'soc'):
            return False, f"Invalid {mode_key}_limit. Valid values: none, amount, soc"
        return _write_template(d, chargepoint_id, mode_key, ('chargemode', mode_key, 'limit', 'selected'), value,
                               f"Error setting {LIMIT_LABELS[mode_key]} limit: ")
    return handler


def _http_amount(mode_key: str):
    def handler(d, value, chargepoint_id, options):
        if not is_numeric(value):
            return False, f"Invalid amount value: {value}"
        amount = php_floatval(value)
        if amount < 0:
            return False, 'Amount must be >= 0'
        return _write_template(d, chargepoint_id, mode_key, ('chargemode', mode_key, 'limit', 'amount'),
                               int(amount * 1000), f"Error setting {LIMIT_LABELS[mode_key]} amount: ")
    return handler


def _http_soc(mode_key: str):
    def handler(d, value, chargepoint_id, options):
        if not is_numeric(value):
            return False, f"Invalid SoC value: {value}"
        soc = php_intval(value)
        if soc < 0 or soc > 100:
            return False, 'SoC must be between 0 and 100'
        return _write_template(d, chargepoint_id, mode_key, ('chargemode', mode_key, 'limit', 'soc'), soc,
                               f"Error setting {LIMIT_LABELS[mode_key]} SoC: ")
    return handler


def _http_bat_mode(d, value, chargepoint_id, options):
    valid_modes = ['min_soc_bat_mode', 'ev_mode', 'bat_mode']
    if value not in valid_modes:
        return False, 'Invalid bat_mode. Valid modes: ' + ', '.join(valid_modes)
    d._publish("openWB/set/general/chargemode_config/bat/mode", value)
    return True, f"Bat mode set to {value}"


def _http_bat_power_reserve(d, value, chargepoint_id, options):
    if not is_numeric(value):
        return False, f"Invalid bat_power_reserve value: {value}"
    watts = php_intval(value)
    if watts < 0:
        return False, 'bat_power_reserve must be >= 0'
    d._publish("openWB/set/general/chargemode_config/bat/power_reserve", watts)
    return True, f"bat_power_reserve set to {watts}W"


def _http_vehicle(d, value, chargepoint_id, options):
    if not is_numeric(value):
        return False, f"Invalid vehicle ID: {value}"
    vehicle_id = php_intval(value)
    if vehicle_id < 0:
        return False, 'Vehicle ID must be >= 0'
    d._publish(f"openWB/set/chargepoint/{chargepoint_id}/config/ev", str(vehicle_id))
    return True, f"Vehicle {vehicle_id} assigned to chargepoint {chargepoint_id}"


def _http_manual_soc(d, value, chargepoint_id, options):
    if not is_numeric(value):
        return False, f"Invalid SoC value: {value}"
    soc = php_intval(value)
    if soc < 0 or soc > 100:
        return False, 'Manual SoC must be between 0 and 100'
    config = d.raw_value_cache.get(f"openWB/chargepoint/{chargepoint_id}/config")
    if not config:
        return False, ('Error setting manual SoC: No data received for topic: '
                       f"openWB/chargepoint/{chargepoint_id}/config")
    vehicle_id = config.get('ev') if isinstance(config, dict) else None
    if vehicle_id is None:
        return False, 'No vehicle assigned to chargepoint'
    d._publish(f"openWB/set/vehicle/{vehicle_id}/soc_module/calculated_soc_state/manual_soc", str(soc))
    return True, f"Manual SoC set to {soc}% for vehicle {vehicle_id} (chargepoint {chargepoint_id})"


WRITE_DISPATCH: Dict[str, Callable[..., Tuple[bool, str]]] = {
    'set_chargemode': _http_set_chargemode,
    'chargecurrent': _http_template_number(
        'instant_charging', ('chargemode', 'instant_charging', 'current'), php_floatval, 'current',
        'Error setting chargecurrent: '),
    'minimal_pv_soc': _http_template_number(
        'pv_charging', ('chargemode', 'pv_charging', 'min_soc'), php_intval, 'SoC', 'Error setting minimal PV SoC: '),
    'minimal_permanent_current': _http_template_number(
        'pv_charging', ('chargemode', 'pv_charging', 'min_current'), php_floatval, 'current',
        'Error setting minimal permanent current: '),
    'max_price_eco': _http_max_price_eco,
    'chargepoint_lock': lambda d, v, i, o: d._set_chargepoint_lock(i, v),
    'bat_mode': _http_bat_mode,
    'bat_power_reserve': _http_bat_power_reserve,
    'instant_charging_limit': _http_limit('instant_charging'),
    'instant_charging_amount': _http_amount('instant_charging'),
    'instant_charging_soc': _http_soc('instant_charging'),
    'pv_charging_limit': _http_limit('pv_charging'),
    'pv_charging_amount': _http_amount('pv_charging'),
    'pv_charging_soc': _http_soc('pv_charging'),
    'vehicle': _http_vehicle,
    'manual_soc': _http_manual_soc,
    'set_io_output': lambda d, v, i, o: d._set_io_output(i, v, o.get('io_output'), o.get('io_output_type')),
}


class _RecordingCache:
    """dict-like read-only wrapper that remembers every topic a handler asked for."""

    def __init__(self, source: Dict[str, Any], topics: set):
        self._source = source
        self._topics = topics

    def get(self, topic: str, default: Any = None) -> Any:
        if topic in self._source:
            self._topics.add(topic)
        return self._source.get(topic, default)


class _RecordingTemplates:
    def __init__(self, source: Dict[str, Any], topics: set):
        self._source = source
        self._topics = topics

    def get(self, chargepoint_id: str, default: Any = None) -> Any:
        topic = f"openWB/chargepoint/{chargepoint_id}/set/charge_template"
        if chargepoint_id in self._source:
            self._topics.add(topic)
        return self._source.get(chargepoint_id, default)


class ReadView:
    """Per-request stand-in for the daemon in the read handlers. It records the openWB topics behind the
    values that are returned, so the caller's broker permissions can be checked for exactly those topics."""

    def __init__(self, daemon: Any):
        self.topics: set = set()
        # (aggregate topic, per-ID topics): a total is readable with the sum role (e.g. chargepoint-sum-access) or
        # with the roles of all single components
        self.alternatives: List[Tuple[str, set]] = []
        self.lowest_ids = daemon.lowest_ids
        self.all_ids = daemon.all_ids
        self.total_sums = daemon.total_sums
        self.raw_value_cache = _RecordingCache(daemon.raw_value_cache, self.topics)
        self.charge_template_cache = _RecordingTemplates(daemon.charge_template_cache, self.topics)
        self._normalize_io_output_type = daemon._normalize_io_output_type
        self._source = daemon

    def _get_io_output_map(self, io_id: Any, output_type: str) -> Dict[str, Any]:
        value = self.raw_value_cache.get(f"openWB/io/states/{io_id}/get/{output_type}")
        return value if isinstance(value, dict) else {}

    def record_total(self, component: str, field: str) -> None:
        # totals are sums over every ID of a component type, so every contributing topic is read
        pattern = re.compile(rf"^openWB/{re.escape(component)}/\d+/get/{re.escape(field)}$")
        per_id = {t for t in list(self._source.raw_value_cache) if pattern.match(t)}
        self.alternatives.append((f"openWB/{component}/get/{field}", per_id))

    def probe_topics(self) -> set:
        """Every topic the caller's permissions have to be tested for."""
        probe = set(self.topics)
        for aggregate, per_id in self.alternatives:
            probe.add(aggregate)
            probe.update(per_id)
        return probe

    def blocking_topics(self, denied: set) -> List[str]:
        """The topics that keep the caller from reading the whole response, given the denied ones."""
        blocking = [t for t in self.topics if t in denied]
        for aggregate, per_id in self.alternatives:
            aggregate_ok = aggregate in self._source.raw_value_cache and aggregate not in denied
            if not aggregate_ok and (denied & per_id or not per_id):
                blocking.append(aggregate)
        return sorted(blocking)

    def record_components(self) -> None:
        # an ID is visible if one of its get topics is; one per ID is enough
        for type_ in SCAN_TYPES:
            for id_ in discover_ids(self, type_):
                prefix = f"openWB/io/states/{id_}/get/" if type_ == 'io' else f"openWB/{type_}/{id_}/get/"
                topics = sorted(t for t in list(self._source.raw_value_cache) if t.startswith(prefix))
                if topics:
                    self.topics.add(topics[0])


# A component counts as known when its marker topic carries a value (the PHP API scanned these topics):
# (marker topic, value must be numeric)
_ID_MARKERS: Dict[str, Tuple[Any, bool]] = {
    'chargepoint': (re.compile(r'^openWB/chargepoint/(\d+)/get/imported$'), True),
    'bat': (re.compile(r'^openWB/bat/(\d+)/get/imported$'), True),
    'pv': (re.compile(r'^openWB/pv/(\d+)/get/exported$'), True),
    'counter': (re.compile(r'^openWB/counter/(\d+)/get/imported$'), True),
    'consumer': (re.compile(r'^openWB/consumer/(\d+)/module$'), False),
    'io': (re.compile(r'^openWB/io/states/(\d+)/get/digital_output$'), False),
    'io_input': (re.compile(r'^openWB/io/states/(\d+)/get/(?:digital|analog)_input$'), False),
}


def _marker_has_value(value: Any, numeric: bool) -> bool:
    if value is None or (isinstance(value, str) and value == ''):
        return False
    if numeric:
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    return True


def discover_ids(daemon: Any, type_: str) -> List[int]:
    source = getattr(daemon, '_source', daemon)
    pattern, numeric = _ID_MARKERS[type_]
    ids = set()
    for topic, value in list(source.raw_value_cache.items()):
        match = pattern.match(topic)
        if match and _marker_has_value(value, numeric):
            ids.add(int(match.group(1)))
    return sorted(ids)


def auto_id(daemon: Any, type_: str) -> Optional[int]:
    """The ID "auto" stands for: the lowest known one - for counters the grid counter of the hierarchy."""
    source = getattr(daemon, '_source', daemon)
    if type_ == 'counter' and source.primary_ids.get('counter') is not None:
        return source.primary_ids['counter']
    ids = discover_ids(daemon, type_)
    return ids[0] if ids else None


def list_components(daemon: Any) -> Dict[str, List[int]]:
    return {
        TYPE_PUBLIC_NAMES.get(type_, type_): discover_ids(daemon, type_)
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
        if target_id is not None:
            # lowest_ids holds ints, the charge_template cache is keyed by strings
            target_id = str(target_id)
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


def _io_options(all_params: Dict[str, Any]) -> Dict[str, Any]:
    return {'io_output': all_params.get('io_output'), 'io_output_type': all_params.get('io_output_type')}


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
            resolved = auto_id(daemon, id_type)
            if resolved is None:
                return {'success': False, 'message': f"No {id_type} devices available for auto-ID"}
            target_id = resolved

        result = ph.write_parameter(param, value, target_id, _io_options(all_params))

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
    options = _io_options(all_params)

    for param, id_ in read_params.items():
        resolved_id = id_
        if param in GLOBAL_READ_PARAMETERS:
            pass
        elif id_ in ('auto', ''):
            type_ = get_type_from_parameter(param)
            resolved_id = auto_id(ph.daemon, type_)
            if resolved_id is None:
                if debug:
                    debug_info.append(f"Auto-ID failed for {param}: No {type_} devices found via MQTT wildcard scan")
                if type_ == 'chargepoint':
                    resolved_id = 0
                else:
                    continue

        data = ph.read_parameter(param, resolved_id, options)
        if data is not None:
            result.update(data)

    return result, debug_info
