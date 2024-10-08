import os
import time
import logging
from pathlib import Path
import pprint
from typing import Any, Optional
import requests

from control import data
from control.chargepoint.chargepoint import Chargepoint
import dataclass_utils
from helpermodules import subdata
from helpermodules.broker import InternalBrokerClient
from helpermodules.pub import Pub
from helpermodules.utils.run_command import run_command
from helpermodules.utils.topic_parser import decode_payload
from modules.common import req
from modules.common.abstract_device import AbstractDevice

log = logging.getLogger(__name__)


def config_and_state():
    parsed_data = ""
    try:
        secondary = subdata.SubData.general_data.data.extern
    except Exception:
        secondary = False

    with ErrorHandlingContext():
        parent_file = Path(__file__).resolve().parents[2]
        with open(f"{parent_file}/web/version", "r") as f:
            version = f.read().strip()
        with open(f"{parent_file}/web/lastcommit", "r") as f:
            lastcommit = f.read().strip()
        parsed_data += f"# Version\n{version}\n{lastcommit}\n\n"
    with ErrorHandlingContext():
        parsed_data += f"# Cloud/Brücken\n{BrokerContent().get_bridges()}"
    with ErrorHandlingContext():
        chargemode_config = data.data.general_data.data.chargemode_config
        parsed_data += "\n# Allgemein\n"
        if secondary is False:
            parsed_data += (f"Modus: Primary\nHausverbrauch: {data.data.counter_all_data.data.set.home_consumption}W\n"
                            f"Phasenvorgabe: Sofortladen {chargemode_config.instant_charging.phases_to_use}, Zielladen "
                            f"{chargemode_config.scheduled_charging.phases_to_use}, Zeitladen: "
                            f"{chargemode_config.time_charging.phases_to_use}, PV-Laden: "
                            f"{chargemode_config.pv_charging.phases_to_use}, Einschaltschwelle: "
                            f"{chargemode_config.pv_charging.switch_on_threshold}W, Ausschaltschwelle: "
                            f"{chargemode_config.pv_charging.switch_off_threshold}W\n"
                            f"Regelintervall: {data.data.general_data.data.control_interval}s, ")
        else:
            parsed_data += "Modus: Secondary\n"
        parsed_data += f"Display aktiviert: {data.data.optional_data.data.int_display.active}\n"

    if secondary is False:
        with ErrorHandlingContext():
            pretty_hierarchy = pprint.pformat(data.data.counter_all_data.data.get.hierarchy,
                                              indent=4, compact=True, sort_dicts=False, width=100)
            parsed_data += f"\n# Hierarchie\n{pretty_hierarchy}\n"

    with ErrorHandlingContext():
        if secondary:
            with ErrorHandlingContext():
                parsed_data += "\n# Ladepunkte\n"
                for cp in subdata.SubData.cp_data.values():
                    parsed_data += get_parsed_cp_data(cp.chargepoint)
        else:
            parsed_data += "\n# Geräte und Komponenten\n"
            for key, value in data.data.system_data.items():
                with ErrorHandlingContext():
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
                                counter_all_data = data.data.counter_all_data
                                if counter_all_data.get_evu_counter_str() == f"counter{component_data.num}":
                                    parsed_data += (f"{comp_key}: EVU-Zähler -> max. Leistung "
                                                    f"{component_data.data.config.max_total_power}, "
                                                    f"max. Ströme {component_data.data.config.max_currents}; ")
                                elif counter_all_data.data.config.home_consumption_source_id == component_data.num:
                                    parsed_data += (f"{comp_key}: Hausverbrauchszähler -> max. Leistung "
                                                    f"{component_data.data.config.max_total_power}, "
                                                    f"max. Ströme {component_data.data.config.max_currents}; ")
                                else:
                                    parsed_data += f"{key}: max. Ströme {component_data.data.config.max_currents}"
                                parsed_data += (f"Leistung: {component_data.data.get.power/1000}kW, Ströme: "
                                                f"{component_data.data.get.currents}A, Fehlerstatus: "
                                                f"{component_data.data.get.fault_str}\n")
            with ErrorHandlingContext():
                parsed_data += "\n# Ladepunkte\n"
                parsed_data += f"Ladeleistung aller Ladepunkte {data.data.cp_all_data.data.get.power / 1000}kW\n"
                for cp in data.data.cp_data.values():
                    parsed_data += get_parsed_cp_data(cp)
    return parsed_data


def get_parsed_cp_data(cp: Chargepoint) -> str:
    parsed_data = ""
    with ErrorHandlingContext():
        if hasattr(cp.chargepoint_module.config.configuration, "ip_address"):
            ip = cp.chargepoint_module.config.configuration.ip_address
        else:
            ip = None
        parsed_data += (f"LP{cp.num}: Typ: {cp.chargepoint_module.config.type}; IP: "
                        f"{ip}; Stecker-Status: {cp.data.get.plug_state}, Leistung: "
                        f"{cp.data.get.power/1000}kW, {cp.data.get.currents}A, {cp.data.get.voltages}V, Lademodus: "
                        f"{cp.data.control_parameter.chargemode}, Submode: "
                        f"{cp.data.control_parameter.submode}, Soll-Strom: "
                        f"{cp.data.set.current}A, Status: {cp.data.get.state_str}, "
                        f"Fehlerstatus: {cp.data.get.fault_str}\n")
        if cp.chargepoint_module.config.type == "openwb_pro":
            try:
                parsed_data += f"{req.get_http_session().get(f'http://{ip}/connect.php', timeout=5).text}\n"
            except requests.Timeout:
                parsed_data += "Timeout beim Abrufen der Daten\n"
    return parsed_data


openwb_base_dir = Path(__file__).resolve().parents[2]
ramdisk_dir = openwb_base_dir / 'ramdisk'
debug_file = ramdisk_dir / 'debug.log'


def merge_log_files(log_name, num_lines):
    log_files = [f"{ramdisk_dir}/{log_name}.log.{i}" for i in range(5, 1)]
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


def create_debug_log(input_data):
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
        header = (f"{input_data['message']}\n{debug_email}\n{input_data['serialNumber']}\n"
                  f"{input_data['installedComponents']}\n{input_data['vehicles']}\n")
        with open(debug_file, 'w+') as df:
            write_to_file(df, lambda: header)
            write_to_file(df, lambda: f"## section: configuration and state ##\n{config_and_state()}\n")
            write_to_file(df, lambda: f'## section: system ##\n{run_command(["uptime"])}{run_command(["free"])}\n')
            write_to_file(df, lambda: f"## section: uuids ##\n{get_uuids()}\n")
            write_to_file(df, lambda: f'## section: network ##\n{run_command(["ifconfig"])}\n')
            write_to_file(df, lambda: f'## section: storage ##\n{run_command(["df", "-h"])}\n')
            write_to_file(df, lambda: f"## section: broker essentials ##\n{broker.get_broker_essentials()}\n")
            write_to_file(
                df, lambda: f"## section: retained log ##\n{merge_log_files('main', 500)}")
            write_to_file(df, lambda: "## section: info log ##\n")
            Pub().pub('openWB/set/system/debug_level', 20)
            time.sleep(60)
            write_to_file(df, lambda: merge_log_files("main", 1000))
            write_to_file(df, lambda: "## section: debug log ##\n")
            Pub().pub('openWB/set/system/debug_level', 10)
            time.sleep(60)
            write_to_file(df, lambda: merge_log_files("main", 2500))
            write_to_file(
                df,
                lambda: f'## section: internal chargepoint log ##\n{merge_log_files("internal_chargepoint", 1000)}\n')
            write_to_file(df, lambda: f'## section: mqtt log ##\n{merge_log_files("mqtt", 1000)}\n')
            write_to_file(df, lambda: f'## section: soc log ##\n{merge_log_files("soc", 1000)}\n')
            write_to_file(df, lambda: f'## section: charge log ##\n{merge_log_files("chargelog", 1000)}\n')
            write_to_file(df, lambda: f"## section: broker ##\n{broker.get_broker()}")

        log.info("***** uploading debug log...")
        with open(debug_file, 'rb') as f:
            data = f.read()
        req.get_http_session().put("https://openwb.de/tools/debug2.php",
                                   data=data,
                                   params={'debugemail': debug_email})

        log.info("***** cleanup...")
        os.remove(debug_file)
        log.info("***** debug log end")
    except Exception as e:
        log.exception(f"Error creating debug log: {e}")


class BrokerContent:
    def __init__(self) -> None:
        self.content = ""

    def get_broker(self):
        InternalBrokerClient("processBrokerBranch", self.__on_connect_broker, self.__get_content).start_finite_loop()
        return self.content

    def __on_connect_broker(self, client, userdata, flags, rc):
        client.subscribe("openWB/#", 2)

    def __get_content(self, client, userdata, msg):
        self.content += f"{msg.topic} {decode_payload(msg.payload)}\n"

    def get_broker_essentials(self):
        InternalBrokerClient("processBrokerBranch", self.__on_connect_broker_essentials,
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
        client.subscribe("openWB/optional/et/provider", 2)

    def get_bridges(self):
        InternalBrokerClient("processBrokerBranch", self.__on_connect_bridges, self.__get_bridges).start_finite_loop()
        return self.content

    def __on_connect_bridges(self, client, userdata, flags, rc):
        client.subscribe("openWB/system/mqtt/#", 2)

    def __get_bridges(self, client, userdata, msg):
        if "openWB/system/mqtt/bridge" in msg.topic:
            payload = decode_payload(msg.payload)
            self.content += (f"Name: {payload['name']}, aktiv: {payload['active']}, "
                             f"openWB-Cloud: {payload['remote']['is_openwb_cloud']}")
            if payload['remote'].get("is_openwb_cloud"):
                self.content += (f", BN: {payload['remote']['username']}, PW: {payload['remote']['password']}, "
                                 f"Partnerzugang: {payload['access']['partner']}")
            self.content += "\n"
        elif "openWB/system/mqtt/valid_partner_ids":
            self.content += f"Partner-IDs: {decode_payload(msg.payload)}\n"


class ErrorHandlingContext:
    def __init__(self):
        pass

    def __enter__(self):
        return None

    def __exit__(self, exception_type, exception, exception_traceback) -> bool:
        if isinstance(exception, Exception):
            log.exception("Fehler beim Parsen der Daten für das Support-Ticket")
        return True
