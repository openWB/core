import os
import json
import time
import subprocess
import logging
from pathlib import Path
import pprint
from control import data
import dataclass_utils
from helpermodules.pub import Pub
from helpermodules.utils.run_command import run_command
from modules.common.abstract_device import AbstractDevice

log = logging.getLogger(__name__)


def parse_send_debug_data():
    parent_file = Path(__file__).resolve().parents[2]
    with open(f"{parent_file}/web/version", "r") as f:
        version = f.read().strip()
    with open(f"{parent_file}/web/lastcommit", "r") as f:
        lastcommit = f.read().strip()
    parsed_data = (f"# Version\n{version}\n{lastcommit}\n\nCloud-Benutzername"
                   "# Hierarchie\n")
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
                            parsed_data += f"{key}: max. Ströme {component_data.data.config.max_currents}"
                        parsed_data += (f"Leistung: {component_data.data.get.power/1000}kW, Ströme: "
                                        f"{component_data.data.get.currents}A, Fehlerstatus: "
                                        f"{component_data.data.get.fault_str}\n")
        except Exception:
            log.exception("Fehler beim Parsen der Daten für das Support-Ticket")

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

    chargemode_config = data.data.general_data.data.chargemode_config
    parsed_data += (f"\n# Allgemein\nHausverbrauch: {data.data.counter_all_data.data.set.home_consumption}W\n"
                    f"Phasenvorgabe: Sofortladen {chargemode_config.instant_charging.phases_to_use}, Zielladen "
                    f"{chargemode_config.scheduled_charging.phases_to_use}, Zeitladen: "
                    f"{chargemode_config.time_charging.phases_to_use}, PV-Laden: "
                    f"{chargemode_config.pv_charging.phases_to_use}, Einschaltschwelle: "
                    f"{chargemode_config.pv_charging.switch_on_threshold}W, Ausschaltschwelle: "
                    f"{chargemode_config.pv_charging.switch_off_threshold}W\n"
                    f"\nRegelintervall: {data.data.general_data.data.control_interval}s,  Display aktiviert {data.data.optional_data.data.int_display.active}\n")
    return parsed_data


openwb_base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
ramdisk_dir = os.path.join(openwb_base_dir, 'ramdisk')
debug_file = os.path.join(ramdisk_dir, 'debug.log')


def merge_log_files(log_name, num_lines, log_path=None):
    if log_path is None:
        log_path = ramdisk_dir
    log_files = [os.path.join(log_path, f"{log_name}.log.{i}") for i in range(1, 5)]
    log_files.append(os.path.join(log_path, f"{log_name}.log"))

    lines = []
    try:
        # Überprüfe jede Datei und lese sie, wenn sie existiert
        for log_file in log_files:
            if os.path.isfile(log_file):
                with open(log_file, 'r') as file:
                    lines += file.readlines()
    except Exception as e:
        logging.error(f"Fehler beim Lesen der Logdateien: {e}")
    return ''.join(lines[-num_lines:])


def get_uuids():
    try:
        with open(openwb_base_dir + 'data/log/uuid', 'r') as uuid_file:
            return (uuid_file.read())
    except Exception as e:
        logging.error(f"Error reading UUID file: {e}")


def create_debug_log(input_data):
    try:
        data = json.loads(input_data)  # Assuming input_data is provided as JSON string
        debug_email = data.get('email', '')
        with open(debug_file, 'w') as df:
            df.write(f"{data.get('message', '')}\n")
            df.write(f"{debug_email}\n")
            df.write(f"{data.get('serialNumber', '')}\n")
            df.write(f"{data.get('installedComponents', '')}\n")
            df.write(f"{data.get('vehicles', '')}\n")
            df.write(f"# section: configuration and state #\n{config_and_state}\n")
            df.write(f'# section: system #\n{run_command("uptime")}{run_command("free")}')
            df.write(f'# section: network #\n{run_command("ifconfig")}')
            df.write(f'# section: storage #\n{run_command("df -h")}')
            df.write(f"# section: uuids #\n{get_uuids()}")
            df.write("# section: broker #\n")
            df.write(run_command("timeout 1 mosquitto_sub -v -t 'openWB/#'"))
            df.write("# section: broker essentials #\n")
            # ToDo section
            df.write("# section: retained log #\n")
            df.write(merge_log_files("main", 500))
            df.write("# section: info log #\n")
            Pub().pub('openWB/set/system/debug_level', 20)
            time.sleep(60)
            df.write(merge_log_files("main", 1000))
            df.write("# section: debug log #\n")
            Pub().pub('openWB/set/system/debug_level', 10)
            time.sleep(60)
            df.write(merge_log_files("main", 2500))
            df.write(f'# section: storage #\n{run_command("df -h")}')
            df.write(f'# section: storage # {run_command("df -h")}\n')
            df.write(f'# section: internal chargepoint log # {merge_log_files("internal_chargepoint", 1000)}\n')
            df.write(f'# section: mqtt log # {merge_log_files("mqtt", 1000)}\n')
            df.write(f'# section: soc log # {merge_log_files("soc", 1000)}\n')
            df.write(f'# section: charge log # {merge_log_files("chargelog", 1000)}\n')

        # Upload debug file
        logging.info("***** uploading debug log...")
        # Assuming curl command is replaced with Python requests library
        # requests.post("https://openwb.de/tools/debug2.php", files={'debugfile': open(debug_file, 'rb')}, params={'debugemail': debug_email})

        # Cleanup
        logging.info("***** cleanup...")
        os.remove(debug_file)
        logging.info("***** debug log end")

    except Exception as e:
        logging.error(f"Error creating debug log: {e}")


# Example usage
input_data = '{"message": "example message", "email": "example@example.com", "serialNumber": "123456", "installedComponents": "component1, component2", "vehicles": "vehicle1, vehicle2"}'
config_and_state = "example configuration and state"
create_debug_log(input_data, config_and_state)
