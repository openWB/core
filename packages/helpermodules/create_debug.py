import os
import time
import logging
from pathlib import Path
from typing import Any, Optional
import requests

from control import data
from control.chargepoint.chargepoint import Chargepoint
import dataclass_utils
from helpermodules import subdata
from helpermodules.broker import BrokerClient
from helpermodules.pub import Pub
from helpermodules.utils.run_command import run_command, run_shell_command
from helpermodules.utils.topic_parser import decode_payload
from modules.common import req
from modules.common.abstract_device import AbstractDevice

log = logging.getLogger(__name__)


def get_common_data():
    parsed_data = ""
    try:
        serial_number = subdata.SubData.system_data["system"].data["serial_number"]
    except Exception:
        serial_number = None
    try:
        mac_address = subdata.SubData.system_data["system"].data["mac_address"]
    except Exception:
        mac_address = None
    try:
        ip_address = subdata.SubData.system_data["system"].data["ip_address"]
    except Exception:
        ip_address = None
    try:
        updateAvailable = subdata.SubData.system_data["system"].data["current_branch_commit"] and \
            subdata.SubData.system_data["system"].data["current_branch_commit"] != \
            subdata.SubData.system_data["system"].data["current_commit"]
    except Exception:
        updateAvailable = False

    with ErrorHandlingContext():
        parsed_data += f"Firmware_deprecated: {updateAvailable}\n"
    with ErrorHandlingContext():
        parent_file = Path(__file__).resolve().parents[2]
        with open(f"{parent_file}/web/version", "r") as f:
            version = f.read().strip()
        with open(f"{parent_file}/web/lastcommit", "r") as f:
            lastcommit = f.read().strip()
        parsed_data += f"Version: {version} ({lastcommit})\n"
    with ErrorHandlingContext():
        if serial_number is None or serial_number == "null":
            parsed_data += "openWB_Serial: unknown\n"
        else:
            parsed_data += f"openWB_Serial: {serial_number}\n"
    with ErrorHandlingContext():
        parsed_data += f"IP_Address: {ip_address}\n"
    with ErrorHandlingContext():
        parsed_data += f"MAC_Address: {mac_address}\n"
    return parsed_data


def get_hardware_data():
    parsed_data = ""
    temp = run_shell_command(["vcgencmd measure_temp"]).removeprefix("temp=").removesuffix("\n")
    throttled = int(run_shell_command("vcgencmd get_throttled").removeprefix("throttled="), 16)
    parsed_data += f"Temperature_C: {temp}"
    mask_undervoltage = 0b0001
    mask_temp_limit = 0b1000
    mask_undervoltage_reboot = 0x10000
    mask_temp_limit_reboot = 0x80000
    if throttled & mask_temp_limit:
        parsed_data += ", aktuell: Soft Temperature Limit"
    else:
        parsed_data += ", aktuell: okay"
    if throttled & mask_temp_limit_reboot:
        parsed_data += ", seit Reboot: Soft Temperature Limit\n"
    else:
        parsed_data += ", seit Reboot: okay\n"

    parsed_data += "RPI_Voltage: "
    if throttled & mask_undervoltage:
        parsed_data += "aktuell: Undervoltage (< 4.63V)"
    else:
        parsed_data += "aktuell: okay"
    if throttled & mask_undervoltage_reboot:
        parsed_data += ", seit Reboot: Undervoltage (< 4.63V)"
    else:
        parsed_data += ", seit Reboot: okay"
    return parsed_data


def config_and_state():
    parsed_data = ""
    try:
        secondary = subdata.SubData.general_data.data.extern
    except Exception:
        secondary = False

    parsed_data += "## General ##\n"
    with ErrorHandlingContext():
        parsed_data += f"openWB_Cloud: {BrokerContent().get_cloud()}"
        if secondary is False:
            parsed_data += ("Mode: Primary\n"
                            f"Home_Consumption: {data.data.counter_all_data.data.set.home_consumption} W\n"
                            f"Control_Interval: {data.data.general_data.data.control_interval}s\n")
        else:
            parsed_data += "Mode: Secondary\n"
        parsed_data += f"Display_Active: {data.data.optional_data.data.int_display.active}\n"
    if secondary is False:
        with ErrorHandlingContext():
            chargemode_config = data.data.general_data.data.chargemode_config
            parsed_data += (
                "\n## General Charge Config/ PV ##\n"
                f"Phase_Switch_Delay: {chargemode_config.pv_charging.phase_switch_delay} min\n"
                f"Retry_Failed_Phase_Switches: {chargemode_config.pv_charging.retry_failed_phase_switches}\n"
                f"Control_Range: {chargemode_config.pv_charging.control_range}W\n"
                f"Switch_On_Threshold: {chargemode_config.pv_charging.switch_on_threshold}W\n"
                f"Switch_On_Delay: {chargemode_config.pv_charging.switch_on_delay}s\n"
                f"Switch_Off_Threshold: {chargemode_config.pv_charging.switch_off_threshold}W\n"
                f"Switch_Off_Delay: {chargemode_config.pv_charging.switch_off_delay}s\n"
                f"Feed_In_Yield: {chargemode_config.feed_in_yield}W\n"
                f"Feed_In_Limit_Vehicle: {chargemode_config.pv_charging.feed_in_limit}W\n"
                f"Bat_Mode: {chargemode_config.pv_charging.bat_mode}\n"
                f"Min_Bat_SoC: {chargemode_config.pv_charging.min_bat_soc}%\n"
                f"Bat_Power_Reserve_Active: {chargemode_config.pv_charging.bat_power_reserve_active}\n"
                f"Bat_Power_Reserve: {chargemode_config.pv_charging.bat_power_reserve}W\n"
                f"Bat_Power_Discharge_Active: {chargemode_config.pv_charging.bat_power_discharge_active}\n"
                f"Bat_Power_Discharge: {chargemode_config.pv_charging.bat_power_discharge}W\n")
    if secondary is False:
        with ErrorHandlingContext():
            parsed_data += f"\n## Hierarchy ##\n{get_hierarchy(data.data.counter_all_data.data.get.hierarchy)}\n"

    with ErrorHandlingContext():
        if secondary:
            with ErrorHandlingContext():
                parsed_data += "\n## Charge Points ##\n"
                for cp in subdata.SubData.cp_data.values():
                    parsed_data += get_parsed_cp_data(cp.chargepoint)
        else:
            parsed_data += "\n## Devices and Components ##\n"
            for key, value in data.data.system_data.items():
                with ErrorHandlingContext():
                    if isinstance(value, AbstractDevice):
                        parsed_data += f"| ### {key} ###\n"
                        parsed_data += f"| Device_Type: {value.device_config.type}\n"
                        parsed_data += f"| Device_FN: {value.device_config.name}\n"
                        parsed_data += ("| Device_Config: "
                                        f"{dataclass_utils.asdict(value.device_config.configuration)}\n")
                        for comp_key, comp_value in value.components.items():
                            parsed_data += f"--| #### {comp_key} ####\n"
                            parsed_data += f"--| Component_Type: {comp_value.component_config.type}\n"
                            parsed_data += f"--| Component_FN: {comp_value.component_config.name}\n"
                            parsed_data += ("--| Component_Config: "
                                            f"{dataclass_utils.asdict(comp_value.component_config.configuration)}\n")
                            if "bat" in comp_value.component_config.type:
                                component_data = data.data.bat_data[f"bat{comp_value.component_config.id}"]
                            elif "counter" in comp_value.component_config.type:
                                component_data = data.data.counter_data[f"counter{comp_value.component_config.id}"]
                            elif "inverter" in comp_value.component_config.type:
                                component_data = data.data.pv_data[f"pv{comp_value.component_config.id}"]
                            if "bat" in comp_value.component_config.type:
                                parsed_data += (f"--| Bat_Power: {component_data.data.get.power/1000}kW\n"
                                                f"--| Bat_SoC: {component_data.data.get.soc}%\n"
                                                f"--| Bat_Error_Status: {component_data.data.get.fault_str}\n\n")
                            elif "inverter" in comp_value.component_config.type:
                                parsed_data += (f"--| Inverter_Power: {component_data.data.get.power/1000}kW\n"
                                                f"--| Max_AC_Out: {component_data.data.config.max_ac_out/1000}kW\n"
                                                f"--| Inverter_Error_Status: {component_data.data.get.fault_str}\n\n")
                            else:
                                counter_all_data = data.data.counter_all_data
                                if counter_all_data.get_evu_counter_str() == f"counter{component_data.num}":
                                    parsed_data += ("--| Counter_Type: EVU-Zähler\n"
                                                    "--| Counter_Max_Power: "
                                                    f"{component_data.data.config.max_total_power}\n"
                                                    "--| Counter_Max_Currents: "
                                                    f"{component_data.data.config.max_currents}\n")
                                elif counter_all_data.data.config.home_consumption_source_id == component_data.num:
                                    parsed_data += ("--| Counter_Type: Hausverbrauchszähler\n"
                                                    "--| Counter_Max_Power: "
                                                    f"{component_data.data.config.max_total_power}\n"
                                                    "--| Counter_Max_Currents: "
                                                    f"{component_data.data.config.max_currents}\n")
                                else:
                                    parsed_data += ("--| Counter_Type: Sonstiger Zähler\n--| Counter_Max_Currents: "
                                                    f"{component_data.data.config.max_currents}\n")
                                parsed_data += (f"--| Counter_Power: {component_data.data.get.power/1000}kW\n"
                                                f"--| Counter_Currents: {component_data.data.get.currents}A\n"
                                                f"--| Counter_Error_Status: {component_data.data.get.fault_str}\n\n")
            with ErrorHandlingContext():
                parsed_data += "\n## Total Powers ##\n"
                evu_id = data.data.counter_all_data.get_id_evu_counter()
                try:
                    evu_powers = filter_log_file('mqtt', 'openWB/counter/' + str(evu_id) + '/get/power,', 5)
                except Exception:
                    evu_powers = "Keine Daten"
                parsed_data += f"EVU_Power:\n{evu_powers}\n"
                try:
                    bat_powers = filter_log_file('mqtt', 'openWB/bat/get/power,', 5)
                except Exception:
                    bat_powers = "Keine Daten"
                parsed_data += f"Bat_All_Power:\n{bat_powers}\n"
                try:
                    pv_powers = filter_log_file('mqtt', 'openWB/pv/get/power,', 5)
                except Exception:
                    pv_powers = "Keine Daten"
                parsed_data += f"PV_All_Power:\n{pv_powers}\n"
                try:
                    cp_powers = filter_log_file('mqtt', 'openWB/chargepoint/get/power,', 5)
                except Exception:
                    cp_powers = "Keine Daten"
                parsed_data += f"CP_All_Power:\n{cp_powers}\n"
                try:
                    home_consumption = filter_log_file('mqtt', 'openWB/counter/set/home_consumption', 5)
                except Exception:
                    home_consumption = "Keine Daten"
                parsed_data += f"Home_Consumption:\n {home_consumption}\n"
            with ErrorHandlingContext():
                parsed_data += "\n## Charge Points ##\n"
                parsed_data += f"CP_All_Power: {data.data.cp_all_data.data.get.power / 1000}kW\n\n"
                for cp in data.data.cp_data.values():
                    parsed_data += get_parsed_cp_data(cp)
    return parsed_data


def get_hierarchy(hierarchy, level=0):
    # get friendly names of elements
    parsed_data = ""
    for element in hierarchy:
        parsed_data += "-" * (level * 2) + "| "
        if element["type"] == "cp":
            try:
                cp = data.data.cp_data[f"cp{element['id']}"].chargepoint_module.config
                parsed_data += f"{element['type']}: {cp.name} (ID: {element['id']})\n"
            except Exception:
                parsed_data += f"{element['type']} (ID: {element['id']})\n"
        else:
            try:
                for key, value in data.data.system_data.items():
                    with ErrorHandlingContext():
                        if isinstance(value, AbstractDevice):
                            for comp_key, comp_value in value.components.items():
                                if (f"component{element['id']}" == comp_key):
                                    parsed_data += (f"{element['type']}: {comp_value.component_config.name} "
                                                    f"(device_type: {value.device_config.type}, ")
                                    if "counter" in comp_value.component_config.type:
                                        component_data = data.data.counter_data[
                                            f"counter{comp_value.component_config.id}"]
                                        counter_all_data = data.data.counter_all_data
                                        if counter_all_data.get_evu_counter_str() == f"counter{component_data.num}":
                                            counter_type = ("EVU-Zähler")
                                        elif (counter_all_data.data.config.home_consumption_source_id ==
                                              component_data.num):
                                            counter_type = ("Hausverbrauchszähler")
                                        else:
                                            counter_type = "Sonstiger Zähler"
                                        parsed_data += f"counter_type: {counter_type}, "
                                    elif "inverter" in comp_value.component_config.type:
                                        component_data = data.data.pv_data[f"pv{comp_value.component_config.id}"]
                                        parsed_data += f"max_ac_out: {component_data.data.config.max_ac_out/1000}kW, "
                                    parsed_data += f"ID: {element['id']})\n"
            except Exception:
                parsed_data += f"{element['type']} (ID: {element['id']})\n"
        if element["children"]:
            parsed_data += get_hierarchy(element["children"], level + 1)
    return parsed_data


def get_parsed_cp_data(cp: Chargepoint) -> str:
    parsed_data = ""
    with ErrorHandlingContext():
        if hasattr(cp.chargepoint_module.config.configuration, "ip_address"):
            ip = cp.chargepoint_module.config.configuration.ip_address
        else:
            ip = None
        if hasattr(cp.chargepoint_module.config.configuration, "mode"):
            mode = f"CP_Mode: {cp.chargepoint_module.config.configuration.mode}\n"
        else:
            mode = ""
        if hasattr(cp.data.get, "frequency"):
            frequency = cp.data.get.frequency
        else:
            frequency = None

        try:
            currents = filter_log_file('mqtt', 'openWB/chargepoint/' +
                                       str(cp.chargepoint_module.config.id) + '/get/currents')
            voltages = filter_log_file('mqtt', 'openWB/chargepoint/' +
                                       str(cp.chargepoint_module.config.id) + '/get/voltages')
        except Exception:
            currents = "Keine Daten"
            voltages = "Keine Daten"
        try:
            ct_id = cp.data.config.template
            max_current_single_phase = data.data.cp_template_data.get(f"cpt{ct_id}").data.max_current_single_phase
            max_current_multi_phases = data.data.cp_template_data.get(f"cpt{ct_id}").data.max_current_multi_phases
        except Exception:
            ct_id = None
            max_current_single_phase = None
        ev_fn = data.data.ev_data.get(f'ev{cp.data.config.ev}').data.name

        parsed_data += f"### LP{cp.num} ###\n"
        if cp.chargepoint_module.config.type == "external_openwb":
            parsed_data += (f"CP_Current_Branch: {cp.data.get.current_branch}\n"
                            f"CP_Version: {cp.data.get.version}\n")
        parsed_data += (f"CP_Type: {cp.chargepoint_module.config.type}\n"
                        f"CP_FN: {cp.chargepoint_module.config.name}\n"
                        f"{mode}"
                        f"CP_Phase_Switch_HW: {cp.data.config.auto_phase_switch_hw}\n"
                        f"CP_Control_Pilot_HW: {cp.data.config.control_pilot_interruption_hw}\n"
                        f"CP_IP: {ip}\n"
                        f"CP_Set_Current: {cp.data.set.current} A\n"
                        f"CPT_Max_Current_Single_Phase: {max_current_single_phase} A\n"
                        f"CPT_Max_Current_Multi_Phases: {max_current_multi_phases} A\n"
                        f"Meter_Power: {cp.data.get.power} W\n"
                        f"Meter_Voltages: {cp.data.get.voltages} V\n"
                        f"Meter_Currents: {cp.data.get.currents} A\n"
                        f"Meter_Frequency: {frequency} Hz\n"
                        f"Meter_Serial: {cp.data.get.serial_number}\n"
                        f"Meter_Imported: {cp.data.get.imported} Wh\n"
                        f"EVSE_Max_Current: {cp.data.get.max_evse_current} A\n"
                        f"EVSE_Current: {cp.data.get.evse_current} A\n"
                        # EVSE_MODBUS: True / False
                        # EVSE_ID: 105 (...)
                        # EVSE_SELFTEST: Passed / Failed
                        f"EVSE_Plug_State: {cp.data.get.plug_state}\n"
                        f"Charge_Mode: {cp.data.control_parameter.chargemode}\n"
                        f"Charge_Submode: {cp.data.control_parameter.submode}\n"
                        f"Charge_State: {cp.data.get.state_str}\n"
                        # CP_SW_VERSION: 2.1.7-Patch.2
                        # CP_FIRMWARE: 1.2.3 (bei Pro bzw. Satellit)
                        # CP_SIGNALING_PRO: basic iec61851 iso11518
                        f"Connected_Vehicle: {ev_fn} (ID: {cp.data.config.ev})\n"
                        f"Charge_Template: {cp.data.set.charge_template.data.name}"
                        f"(ID: {cp.data.set.charge_template.data.id})\n"
                        # f"EV_FN2: {cp.chargepoint_module.get.connected_verhicle.info.name}\n"
                        f"CP_Error_State: {cp.data.get.fault_str}\n"
                        f"Additional_Meter_Voltages: \n{voltages}"
                        f"Additional_Meter_Currents: \n{currents}\n")
        if cp.chargepoint_module.config.type == "openwb_pro":
            try:
                parsed_data += f"openWB_Pro: {req.get_http_session().get(f'http://{ip}/connect.php', timeout=5).text}\n"
            except requests.Timeout:
                parsed_data += "Timeout beim Abrufen der Daten\n"
    return parsed_data


openwb_base_dir = Path(__file__).resolve().parents[2]
ramdisk_dir = openwb_base_dir / 'ramdisk'
debug_file = ramdisk_dir / 'debug.log'


def filter_log_file(log_name, pattern, num_results=10):
    log_files = [f"{ramdisk_dir}/{log_name}.log.{i}" for i in range(5, 0, -1)]
    log_files.append(f"{ramdisk_dir}/{log_name}.log")
    lines = []
    try:
        for log_file in log_files:
            if os.path.isfile(log_file):
                with open(log_file, 'r') as file:
                    for line in file.readlines():
                        if pattern in line:
                            lines.append(line)
    except Exception as e:
        log.exception(f"Fehler beim Lesen der Logdateien: {e}")
    return ''.join(lines[-num_results:])


def merge_log_files(log_name, num_lines):
    log_files = [f"{ramdisk_dir}/{log_name}.log.{i}" for i in range(5, 0, -1)]
    log_files.append(f"{ramdisk_dir}/{log_name}.log")

    lines = []
    try:
        for log_file in log_files:
            if os.path.isfile(log_file):
                with open(log_file, 'r') as file:
                    lines += file.readlines()
    except Exception as e:
        log.exception(f"Fehler beim Lesen der Logdateien: {e}")
    return ''.join(lines[-num_lines:])


def get_uuids():
    try:
        with open(openwb_base_dir / 'data/log/uuid', 'r') as uuid_file:
            return (uuid_file.read())
    except Exception as e:
        log.exception(f"Error reading UUID file: {e}")


def get_boots(num_lines=100):
    lines = []
    log_file = openwb_base_dir / 'data/log/boot'
    try:
        if os.path.isfile(log_file):
            with open(log_file, 'r') as file:
                lines = file.readlines()
    except Exception as e:
        log.exception(f"Error reading BOOT file: {e}")
    return ''.join(lines[-num_lines:])


def create_debug_log(input_data) -> Optional[dict]:
    def write_to_file(file_handler, func, default: Optional[Any] = None):
        try:
            file_handler.write(func()+"\n")
        except Exception as e:
            log.exception(f"Error getting value for chargelog: {func}. Setting to default {default}.")
            file_handler.write(f"Error getting value for chargelog: {func}. Setting to default {default}.\n"
                               f"Error: {e}\n")

    try:
        broker = BrokerContent()
        debug_email = input_data.get('email', '')
        ticketnumber = input_data.get('ticketNumber', '')
        subject = input_data.get('subject', '')
        header = (f"{input_data['message']}\n{debug_email}\n{input_data['serialNumber']}\n"
                  f"{input_data['installedComponents']}\n{input_data['vehicles']}\n")
        if ticketnumber is not None and ticketnumber != "":
            header += f"Ticketnumber: {ticketnumber}\n"
        with open(debug_file, 'w+') as df:
            write_to_file(df, lambda: "# section: form data #")
            write_to_file(df, lambda: header)
            write_to_file(df, lambda: f'# section: system #\n{get_common_data()}'
                                      f'Kernel: {run_shell_command("uname -s -r -v -m -o")}\n'
                                      f'Uptime:{run_command(["uptime"])}{run_command(["free"])}\n')
            write_to_file(df, lambda: f'# section: hardware #\n{get_hardware_data()}')
            write_to_file(df, lambda: f'USB_Devices:\n{run_shell_command(["lsusb"])}\n')
            write_to_file(df, lambda: f"# section: configuration and state #\n{config_and_state()}")
            write_to_file(df, lambda: f"# section: errors #\n{filter_log_file('main', 'ERROR', 30)}\n")
            write_to_file(df, lambda: f"# section: uuids #\n{get_uuids()}\n")
            write_to_file(df, lambda: f"# section: boots #\n{get_boots(30)}\n")
            write_to_file(df, lambda: f'# section: storage #\n{run_command(["df", "-h"])}\n')
            write_to_file(df, lambda: 'Extended_Debug_Section\n')
            write_to_file(df, lambda: f"# section: broker essentials #\n{broker.get_broker_essentials()}\n")
            write_to_file(
                df, lambda: f"# section: retained log #\n{merge_log_files('main', 500)}")
            write_to_file(df, lambda: "# section: info log #\n")
            Pub().pub('openWB/set/system/debug_level', 20)
            time.sleep(60)
            write_to_file(df, lambda: merge_log_files("main", 1000))
            write_to_file(df, lambda: "# section: debug log #\n")
            Pub().pub('openWB/set/system/debug_level', 10)
            time.sleep(60)
            write_to_file(df, lambda: merge_log_files("main", 2500))
            write_to_file(
                df,
                lambda: f'# section: internal chargepoint log #\n{merge_log_files("internal_chargepoint", 1000)}\n')
            write_to_file(df, lambda: f'# section: mqtt log #\n{merge_log_files("mqtt", 1000)}\n')
            write_to_file(df, lambda: f'# section: soc log #\n{merge_log_files("soc", 1000)}\n')
            write_to_file(df, lambda: f'# section: charge log #\n{merge_log_files("chargelog", 1000)}\n')
            write_to_file(df, lambda: f"# section: broker #\n{broker.get_broker()}")
            write_to_file(df, lambda: f'# section: network #\n{run_command(["ip", "-s", "address"])}\n')

        log.info("***** uploading debug log...")
        with open(debug_file, 'rb') as f:
            data = f.read()
            json_rsp = req.get_http_session().put("https://debughandler.wb-solution.de",
                                                  data=data,
                                                  params={
                                                    'debugemail': debug_email,
                                                    'ticketnumber': ticketnumber,
                                                    'subject': subject
                                                  },
                                                  timeout=10).json()

        log.info("***** cleanup...")
        os.remove(debug_file)
        log.info("***** debug log end")
        return json_rsp
    except Exception as e:
        log.exception(f"Error creating debug log: {e}")
        return None


class BrokerContent:
    def __init__(self) -> None:
        self.content = ""
        self.count = 0

    def get_broker(self):
        BrokerClient("processBrokerBranch", self.__on_connect_broker, self.__get_content).start_finite_loop()
        return self.content

    def __on_connect_broker(self, client, userdata, flags, rc):
        client.subscribe("openWB/#", 2)

    def __get_content(self, client, userdata, msg):
        self.content += f"{msg.topic} {decode_payload(msg.payload)}\n"

    def get_broker_essentials(self):
        BrokerClient("processBrokerBranch", self.__on_connect_broker_essentials,
                     self.__get_content).start_finite_loop()
        return self.content

    def __on_connect_broker_essentials(self, client, userdata, flags, rc):
        client.subscribe("openWB/system/ip_address", 2)
        client.subscribe("openWB/system/current_commit", 2)
        client.subscribe("openWB/system/boot_done", 2)
        client.subscribe("openWB/system/update_in_progress", 2)
        client.subscribe("openWB/system/device/#", 2)
        client.subscribe("openWB/system/time", 2)
        client.subscribe("openWB/chargepoint/#", 2)
        client.subscribe("openWB/internal_chargepoint/#", 2)
        client.subscribe("openWB/vehicle/#", 2)
        client.subscribe("openWB/counter/#", 2)
        client.subscribe("openWB/pv/#", 2)
        client.subscribe("openWB/bat/#", 2)
        client.subscribe("openWB/optional/ep/flexible_tariff/provider", 2)

    def __on_connect_bridges(self, client, userdata, flags, rc):
        client.subscribe("openWB/system/mqtt/#", 2)

    def get_cloud(self):
        BrokerClient("processBrokerBranch", self.__on_connect_bridges, self.__get_cloud).start_finite_loop()
        BrokerClient("processBrokerBranch", self.__on_connect_bridges, self.__get_partner).start_finite_loop()
        self.content += f"Active_MQTT_Bridges: {self.count}\n"
        return self.content

    def __get_cloud(self, client, userdata, msg):
        if "openWB/system/mqtt/bridge" in msg.topic:
            payload = decode_payload(msg.payload)
            if payload['active']:
                if payload['remote'].get("is_openwb_cloud"):
                    self.content += f"BN: {payload['remote']['username']}, PW: {payload['remote']['password']}, "
                    if payload['access']['partner']:
                        self.content += "Partnerzugang: An\n"
                    else:
                        self.content += "Partnerzugang: Aus\n"
                else:
                    self.count += 1

    def __get_partner(self, client, userdata, msg):
        if "openWB/system/mqtt/valid_partner_ids" in msg.topic:
            self.content += f"Partner_ID: {decode_payload(msg.payload)}\n"


class ErrorHandlingContext:
    def __init__(self):
        pass

    def __enter__(self):
        return None

    def __exit__(self, exception_type, exception, exception_traceback) -> bool:
        if isinstance(exception, Exception):
            log.exception("Fehler beim Parsen der Daten für das Support-Ticket")
        return True
