#!/usr/bin/env python3
"""Starten der benötigten Prozesse
"""
# flake8: noqa: F402
import logging
from helpermodules import logger
from helpermodules.utils import thread_handler
# als erstes logging initialisieren, damit auch ImportError geloggt werden
logger.setup_logging()
log = logging.getLogger()

from pathlib import Path
from random import randrange
import schedule
import time
import threading
import traceback
from threading import Thread
from control.chargelog.chargelog import calculate_charge_cost

from helpermodules.changed_values_handler import ChangedValuesContext
from helpermodules.measurement_logging.update_yields import update_daily_yields, update_pv_monthly_yearly_yields
from helpermodules.measurement_logging.write_log import LogType, save_log
from modules import loadvars
from modules import configuration
from helpermodules import timecheck, update_config
from helpermodules import subdata
from helpermodules import setdata
from helpermodules import command
from helpermodules.modbusserver import start_modbus_server
from helpermodules.pub import Pub
from control import prepare
from control import data
from control import process
from control.algorithm import algorithm
from helpermodules.utils import exit_after
from modules import update_soc
from modules.internal_chargepoint_handler.internal_chargepoint_handler import GeneralInternalChargepointHandler
from modules.internal_chargepoint_handler.rfid import RfidReader
from modules.utils import wait_for_module_update_completed
from smarthome.smarthome import readmq, smarthome_handler


class HandlerAlgorithm:
    def __init__(self):
        self.interval_counter = 1
        self.current_day = None

    def handler10Sec(self):
        """ führt den Algorithmus durch.
        """
        try:
            @exit_after(data.data.general_data.data.control_interval)
            def handler_with_control_interval():
                if (data.data.general_data.data.control_interval / 10) == self.interval_counter:
                    data.data.copy_data()
                    loadvars_.get_values()
                    wait_for_module_update_completed(loadvars_.event_module_update_completed,
                                                     "openWB/set/system/device/module_update_completed")
                    data.data.copy_data()
                    with ChangedValuesContext(loadvars_.event_module_update_completed):
                        self.heartbeat = True
                        if data.data.system_data["system"].data["perform_update"]:
                            data.data.system_data["system"].perform_update()
                            return
                        elif data.data.system_data["system"].data["update_in_progress"]:
                            log.info("Regelung pausiert, da ein Update durchgeführt wird.")
                        event_global_data_initialized.set()
                        prep.setup_algorithm()
                        control.calc_current()
                        proc.process_algorithm_results()
                        data.data.graph_data.pub_graph_data()
                    self.interval_counter = 1
                else:
                    self.interval_counter = self.interval_counter + 1
            log.info("# ***Start*** ")
            Pub().pub("openWB/set/system/time", timecheck.create_timestamp())
            handler_with_control_interval()
        except KeyboardInterrupt:
            log.critical("Ausführung durch exit_after gestoppt: "+traceback.format_exc())
        except Exception:
            log.exception("Fehler im Main-Modul")

    @exit_after(10)
    def handler5MinAlgorithm(self):
        """ Handler, der alle 5 Minuten aufgerufen wird und die Heartbeats der Threads überprüft und die Aufgaben
        ausführt, die nur alle 5 Minuten ausgeführt werden müssen.
        """
        try:
            with ChangedValuesContext(loadvars_.event_module_update_completed):
                totals = save_log(LogType.DAILY)
                update_daily_yields(totals)
                update_pv_monthly_yearly_yields()
                data.data.general_data.grid_protection()
                data.data.optional_data.et_get_prices()
                data.data.counter_all_data.validate_hierarchy()
        except KeyboardInterrupt:
            log.critical("Ausführung durch exit_after gestoppt: "+traceback.format_exc())
        except Exception:
            log.exception("Fehler im Main-Modul")

    @exit_after(10)
    def handler5Min(self):
        """ Handler, der alle 5 Minuten aufgerufen wird und die Heartbeats der Threads überprüft und die Aufgaben
        ausführt, die nur alle 5 Minuten ausgeführt werden müssen.
        """
        try:
            log.debug("5 Minuten Handler ausführen.")
            if not sub.heartbeat:
                log.error("Heartbeat für Subdata nicht zurückgesetzt.")
                sub.disconnect()
                thread_handler(Thread(target=sub.sub_topics, args=(), name="Subdata"))
            else:
                sub.heartbeat = False

            if not set.heartbeat:
                log.error("Heartbeat für Setdata nicht zurückgesetzt.")
                set.disconnect()
                thread_handler(Thread(target=set.set_data, args=(), name="Setdata"))
            else:
                set.heartbeat = False

            if sub.internal_chargepoint_data["global_data"].configured:
                if not general_internal_chargepoint_handler.internal_chargepoint_handler.heartbeat:
                    log.error("Heartbeat für Internen Ladepunkt nicht zurückgesetzt.")
                    general_internal_chargepoint_handler.event_start.set()
                else:
                    general_internal_chargepoint_handler.internal_chargepoint_handler.heartbeat = False
            with ChangedValuesContext(loadvars_.event_module_update_completed):
                sub.system_data["system"].update_ip_address()
        except KeyboardInterrupt:
            log.critical("Ausführung durch exit_after gestoppt: "+traceback.format_exc())
        except Exception:
            log.exception("Fehler im Main-Modul")

    @exit_after(10)
    def handler_midnight(self):
        try:
            save_log(LogType.MONTHLY)
        except KeyboardInterrupt:
            log.critical("Ausführung durch exit_after gestoppt: "+traceback.format_exc())
        except Exception:
            log.exception("Fehler im Main-Modul")

    @exit_after(10)
    def handler_random_nightly(self):
        try:
            data.data.system_data["system"].thread_backup_and_send_to_cloud()
        except KeyboardInterrupt:
            log.critical("Ausführung durch exit_after gestoppt: "+traceback.format_exc())
        except Exception:
            log.exception("Fehler im Main-Modul")

    @exit_after(10)
    def handler_hour(self):
        try:
            with ChangedValuesContext(loadvars_.event_module_update_completed):
                for cp in data.data.cp_data.values():
                    calculate_charge_cost(cp)
        except KeyboardInterrupt:
            log.critical("Ausführung durch exit_after gestoppt: "+traceback.format_exc())
        except Exception:
            log.exception("Fehler im Main-Modul")


def schedule_jobs():
    [schedule.every().minute.at(f":{i:02d}").do(smarthome_handler).tag("algorithm") for i in range(0, 60, 5)]
    [schedule.every().hour.at(f":{i:02d}").do(handler.handler5Min) for i in range(0, 60, 5)]
    [schedule.every().hour.at(f":{i:02d}").do(handler.handler5MinAlgorithm).tag("algorithm") for i in range(0, 60, 5)]
    [schedule.every().day.at(f"{i:02d}:00").do(handler.handler_hour).tag("algorithm") for i in range(0, 24, 1)]
    # every().hour ruft nicht jede Stunde den Handler auf.
    # schedule.every().hour.do(handler.handler_hour).tag("algorithm")
    schedule.every().day.at("00:00:00").do(handler.handler_midnight).tag("algorithm")
    schedule.every().day.at(f"0{randrange(0, 5)}:{randrange(0, 59):02d}:{randrange(0, 59):02d}").do(
        handler.handler_random_nightly)
    [schedule.every().minute.at(f":{i:02d}").do(handler.handler10Sec).tag("algorithm") for i in range(0, 60, 10)]


try:
    log.debug("Start openWB2.service")
    loadvars_ = loadvars.Loadvars()
    data.data_init(loadvars_.event_module_update_completed)
    update_config.UpdateConfig().update()
    configuration.pub_configurable()

    # run as thread for logging reasons
    t_smarthome = Thread(target=readmq, args=(), name="smarthome")
    t_smarthome.start()
    t_smarthome.join()

    proc = process.Process()
    control = algorithm.Algorithm()
    handler = HandlerAlgorithm()
    prep = prepare.Prepare()
    general_internal_chargepoint_handler = GeneralInternalChargepointHandler()
    rfid = RfidReader()
    event_ev_template = threading.Event()
    event_ev_template.set()
    event_charge_template = threading.Event()
    event_charge_template.set()
    event_cp_config = threading.Event()
    event_cp_config.set()
    event_scheduled_charging_plan = threading.Event()
    event_scheduled_charging_plan.set()
    event_time_charging_plan = threading.Event()
    event_time_charging_plan.set()
    event_soc = threading.Event()
    event_soc.set()
    event_copy_data = threading.Event()  # set: Kopieren abgeschlossen, reset: es wird kopiert
    event_copy_data.set()
    event_global_data_initialized = threading.Event()
    event_command_completed = threading.Event()
    event_command_completed.set()
    event_subdata_initialized = threading.Event()
    event_update_config_completed = threading.Event()
    event_modbus_server = threading.Event()
    event_jobs_running = threading.Event()
    event_jobs_running.set()
    event_update_soc = threading.Event()
    prep = prepare.Prepare()
    soc = update_soc.UpdateSoc(event_update_soc)
    set = setdata.SetData(event_ev_template, event_charge_template,
                          event_cp_config, event_scheduled_charging_plan, event_time_charging_plan, event_soc,
                          event_subdata_initialized)
    sub = subdata.SubData(event_ev_template, event_charge_template,
                          event_cp_config, loadvars_.event_module_update_completed,
                          event_copy_data, event_global_data_initialized, event_command_completed,
                          event_subdata_initialized, soc.event_vehicle_update_completed,
                          event_scheduled_charging_plan, event_time_charging_plan,
                          general_internal_chargepoint_handler.event_start,
                          general_internal_chargepoint_handler.event_stop,
                          event_update_config_completed,
                          event_update_soc,
                          event_soc,
                          event_jobs_running, event_modbus_server)
    comm = command.Command(event_command_completed)
    t_sub = Thread(target=sub.sub_topics, args=(), name="Subdata")
    t_set = Thread(target=set.set_data, args=(), name="Setdata")
    t_comm = Thread(target=comm.sub_commands, args=(), name="Commands")
    t_soc = Thread(target=soc.update, args=(), name="SoC")
    t_internal_chargepoint = Thread(target=general_internal_chargepoint_handler.handler,
                                    args=(), name="Internal Chargepoint")
    if rfid.keyboards_detected:
        t_rfid = Thread(target=rfid.run, args=(), name="Internal Chargepoint")
        t_rfid.start()

    t_sub.start()
    t_set.start()
    t_comm.start()
    t_soc.start()
    t_internal_chargepoint.start()
    threading.Thread(target=start_modbus_server, args=(event_modbus_server,), name="Modbus Control Server").start()
    # Warten, damit subdata Zeit hat, alle Topics auf dem Broker zu empfangen.
    event_update_config_completed.wait(300)
    Pub().pub("openWB/set/system/boot_done", True)
    Path(Path(__file__).resolve().parents[1]/"ramdisk"/"bootdone").touch()
    schedule_jobs()
    if event_jobs_running.is_set():
        # Nach dem Starten als erstes den 10Sek-Handler aufrufen, damit die Werte der data.data initialisiert werden.
        handler.handler10Sec()
except Exception:
    log.exception("Fehler im Main-Modul")

while True:
    try:
        if event_jobs_running.is_set() and len(schedule.get_jobs("algorithm")) == 0:
            schedule_jobs()
        elif event_jobs_running.is_set() is False and len(schedule.get_jobs("algorithm")) > 0:
            schedule.clear("algorithm")
        schedule.run_pending()
        time.sleep(1)
    except Exception:
        log.exception("Fehler im Main-Modul")
