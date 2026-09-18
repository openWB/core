import logging
from typing import Dict, List, Union

from control import data
from modules.common.fault_state_level import FaultStateLevel
from modules.common.utils.component_parser import get_component_name_by_id


control_command_log = logging.getLogger("steuve_control_command")


def check_fault_state_io_device(io_device: int) -> bool:
    return data.data.io_states[f"io_states{io_device}"].data.get.fault_state == FaultStateLevel.ERROR


def get_device_log_message(device: Dict[str, Union[int, str]]) -> str:
    try:
        if device["type"] == "cp":
            cp = f"cp{device['id']}"
            return (f", Ladepunkt {data.data.cp_data[cp].data.config.name}: "
                    f"{data.data.cp_data[cp].data.get.powers}W")
        if device["type"] == "inverter":
            inverter = f"pv{device['id']}"
            return (f", Erzeugungsanlage {get_component_name_by_id(device['id'])}: "
                    f"{data.data.pv_data[inverter].data.get.power}W")
        if device["type"] == "io":
            io = f"io{device['id']}"
            return (f", {data.data.system_data[io].config.name} {device['digital_output']}: "
                    "Leistung unbekannt")
    except KeyError:
        control_command_log.warning(f"Zugriff auf gelöschtes Gerät nicht möglich: {device}")
    except Exception:
        control_command_log.exception(f"Fehler beim Zugriff auf Gerät {device}")
    return f", Unbekanntes Gerät: {device}"


def get_power_log_message(devices: List[Dict[str, Union[int, str]]]) -> str:
    evu_counter = data.data.counter_data[data.data.counter_all_data.get_evu_counter_str()]
    msg = f"EVU-Zähler: {evu_counter.data.get.powers}W, {evu_counter.data.get.power}W"
    for device in devices:
        msg += get_device_log_message(device)
    return msg
