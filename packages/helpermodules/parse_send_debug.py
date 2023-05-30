import logging
import pprint
from control import data
import dataclass_utils
from modules.common.abstract_device import AbstractDevice

log = logging.getLogger(__name__)


def parse_send_debug_data():
    parsed_data = "# Hierarchie\n"
    parsed_data += f"{pprint.pformat(data.data.counter_all_data.data.get.hierarchy, indent=4)}\n"
    parsed_data += "\n# Geräte und Komponenten\n"
    for key, value in data.data.system_data.items():
        try:
            if isinstance(value, AbstractDevice):
                parsed_data += f"{key}: {dataclass_utils.asdict(value.device_config)}\n"
                for comp_key, comp_value in value.components.items():
                    parsed_data += f"{comp_key}: {dataclass_utils.asdict(comp_value.component_config)}\n"
                    if "bat" in comp_value.component_config.type:
                        component_data = data.data.bat_data[f"bat{comp_value.component_config.id}"]
                    elif "counter" in comp_value.component_config.type:
                        component_data = data.data.counter_data[f"counter{comp_value.component_config.id}"]
                    elif "inverter" in comp_value.component_config.type:
                        component_data = data.data.pv_data[f"pv{comp_value.component_config.id}"]
                    if "bat" in comp_value.component_config.type or "inverter" in comp_value.component_config.type:
                        parsed_data += f"Leistung: {component_data.data.get.power/1000}kWh, Fehlerstatus: {component_data.data.get.fault_str}\n"
                    else:
                        parsed_data += f"Leistung: {component_data.data.get.power/1000}kWh, Ströme: {component_data.data.get.currents}A, Fehlerstatus: {component_data.data.get.fault_str}\n"
        except Exception:
            log.exception("Fehler beim Parsen der Daten für das Support-Ticket")

    parsed_data += "\n# Ladepunkte\n"
    parsed_data += f"Ladeleistung aller Ladepunkte {data.data.cp_all_data.data.get.power / 1000}kWh\n"
    for cp in data.data.cp_data.values():
        try:
            parsed_data += f"LP{cp.num}: Steckerstatus: {cp.data.get.plug_state}, Leistung: {cp.data.get.power/1000}kWh, {cp.data.get.currents}A, Lademodus: {cp.data.set.charging_ev_data.data.control_parameter.chargemode}, Submode: {cp.data.set.charging_ev_data.data.control_parameter.submode}, Sollstrom: {cp.data.set.current}A, Status: {cp.data.get.state_str}, Fehlerstatus: {cp.data.get.fault_str}\n"
        except Exception:
            log.exception("Fehler beim Parsen der Daten für das Support-Ticket")

    return parsed_data
