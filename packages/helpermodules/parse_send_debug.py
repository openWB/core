import logging
import pprint
from control import data
import dataclass_utils
from modules.common.abstract_device import AbstractDevice

log = logging.getLogger(__name__)


def parse_send_debug_data():
    parsed_data = "# Hierarchie\n"
    pretty_hierarchy = pprint.pformat(data.data.counter_all_data.data.get.hierarchy,
                                      indent=4, compact=True, sort_dicts=False, width=100)
    parsed_data += f"{pretty_hierarchy}\n"
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
                    if "bat" in comp_value.component_config.type:
                        parsed_data += (f"Leistung: {component_data.data.get.power/1000}kW, "
                                        f"SoC: {component_data.data.get.soc}%, "
                                        f"Fehlerstatus: {component_data.data.get.fault_str}\n")
                    elif "inverter" in comp_value.component_config.type:
                        parsed_data += (f"Leistung: {component_data.data.get.power/1000}kW, "
                                        f"Fehlerstatus: {component_data.data.get.fault_str}\n")
                    else:
                        if data.data.counter_all_data.get_evu_counter_str() == f"counter{component_data.num}":
                            parsed_data += (f"{key}: EVU-Zähler -> max. Leistung "
                                            f"{component_data.data.config.max_total_power}, "
                                            f"max. Ströme {component_data.data.config.max_currents}; ")
                        else:
                            parsed_data += f"{key}: max. Ströme {value.data.config.max_currents}"
                        parsed_data += (f"Leistung: {component_data.data.get.power/1000}kW, Ströme: "
                                        f"{component_data.data.get.currents}A, Fehlerstatus: "
                                        f"{component_data.data.get.fault_str}\n")
        except Exception:
            log.exception("Fehler beim Parsen der Daten für das Support-Ticket")
    parsed_data += f"Hausverbrauch: {data.data.counter_all_data.data.set.home_consumption}W\n"
    chargemode_config = data.data.general_data.data.chargemode_config
    parsed_data += (f"Phasenvorgabe: Sofortladen {chargemode_config.instant_charging.phases_to_use}, Zielladen "
                    f"{chargemode_config.scheduled_charging.phases_to_use}, Zeitladen: "
                    f"{chargemode_config.time_charging.phases_to_use}, PV-Laden: "
                    f"{chargemode_config.pv_charging.phases_to_use}, Einschaltschwelle: "
                    f"{chargemode_config.pv_charging.switch_on_threshold}W, Ausschaltschwelle: "
                    f"{chargemode_config.pv_charging.switch_off_threshold}W\n")

    parsed_data += "\n# Ladepunkte\n"
    parsed_data += f"Ladeleistung aller Ladepunkte {data.data.cp_all_data.data.get.power / 1000}kW\n"
    for cp in data.data.cp_data.values():
        try:
            if hasattr(cp.chargepoint_module.config.configuration, "ip_address"):
                ip = cp.chargepoint_module.config.configuration.ip_address
            else:
                ip = None
            parsed_data += (f"LP{cp.num}: Typ: {cp.chargepoint_module.config.type}; IP: "
                            f"{ip}; Stecker-Status: {cp.data.get.plug_state}, Leistung: "
                            f"{cp.data.get.power/1000}kW, {cp.data.get.currents}A, {cp.data.get.voltages}V, Lademodus: "
                            f"{cp.data.control_parameter.chargemode}, Submode: "
                            f"{cp.data.control_parameter.submode}, Sollstrom: "
                            f"{cp.data.set.current}A, Status: {cp.data.get.state_str}, "
                            f"Fehlerstatus: {cp.data.get.fault_str}\n")
        except Exception:
            log.exception("Fehler beim Parsen der Daten für das Support-Ticket")

    return parsed_data
