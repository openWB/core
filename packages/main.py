#!/usr/bin/env python3
"""Starten der benötigten Prozesse
"""
import logging
import schedule
import time
import threading
import traceback
from threading import Thread

from modules import loadvars
from modules import configuration
from helpermodules import update_config
from helpermodules import subdata
from helpermodules import setdata
from helpermodules import measurement_log
from helpermodules import logger
from helpermodules.logger import cleanup_logfiles
from helpermodules import command
from control import prepare
from control import data
from control import process
from control.algorithm import algorithm
from helpermodules.utils import exit_after
from modules import update_soc
from modules.internal_chargepoint_handler.internal_chargepoint_handler import GeneralInternalChargepointHandler
from modules.internal_chargepoint_handler.rfid import RfidReader
from smarthome.smarthome import readmq, smarthome_handler

logger.setup_logging()
log = logging.getLogger()


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
                    log.setLevel(data.data.system_data["system"].data["debug_level"])
                    loadvars_.get_values()
                    data.data.copy_data()
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
            measurement_log.measurement_log_daily()
            data.data.general_data.grid_protection()
            data.data.optional_data.et_get_prices()
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
                Thread(target=sub.sub_topics, args=()).start()
            else:
                sub.heartbeat = False

            if not set.heartbeat:
                log.error("Heartbeat für Setdata nicht zurückgesetzt.")
                set.disconnect()
                Thread(target=set.set_data, args=()).start()
            else:
                set.heartbeat = False

            if sub.internal_chargepoint_data["global_data"].configured:
                if not general_internal_chargepoint_handler.internal_chargepoint_handler.heartbeat:
                    log.error("Heartbeat für Internen Ladepunkt nicht zurückgesetzt.")
                    general_internal_chargepoint_handler.event_start.set()
                else:
                    general_internal_chargepoint_handler.internal_chargepoint_handler.heartbeat = False

            cleanup_logfiles()
            sub.system_data["system"].update_ip_address()
        except KeyboardInterrupt:
            log.critical("Ausführung durch exit_after gestoppt: "+traceback.format_exc())
        except Exception:
            log.exception("Fehler im Main-Modul")

    @exit_after(10)
    def handler_midnight(self):
        try:
            measurement_log.save_log("monthly")
        except KeyboardInterrupt:
            log.critical("Ausführung durch exit_after gestoppt: "+traceback.format_exc())
        except Exception:
            log.exception("Fehler im Main-Modul")


def schedule_jobs():
    [schedule.every().minute.at(f":{i:02d}").do(handler.handler10Sec).tag("algorithm") for i in range(0, 60, 10)]
    [schedule.every().minute.at(f":{i:02d}").do(soc.update).tag("algorithm") for i in range(0, 60, 10)]
    [schedule.every().minute.at(f":{i:02d}").do(smarthome_handler).tag("algorithm") for i in range(0, 60, 5)]
    [schedule.every().hour.at(f":{i:02d}").do(handler.handler5Min) for i in range(0, 60, 5)]
    [schedule.every().hour.at(f":{i:02d}").do(handler.handler5MinAlgorithm).tag("algorithm") for i in range(1, 60, 5)]
    schedule.every().day.at("00:00:00").do(handler.handler_midnight).tag("algorithm")


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
    rfid0 = RfidReader("event0")
    rfid1 = RfidReader("event1")
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
    event_copy_data = threading.Event()  # set: Kopieren abgeschlossen, reset: es wird kopiert
    event_copy_data.set()
    event_global_data_initialized = threading.Event()
    event_command_completed = threading.Event()
    event_command_completed.set()
    event_subdata_initialized = threading.Event()
    event_jobs_running = threading.Event()
    event_jobs_running.set()
    prep = prepare.Prepare()
    soc = update_soc.UpdateSoc()
    set = setdata.SetData(event_ev_template, event_charge_template,
                          event_cp_config, event_scheduled_charging_plan, event_time_charging_plan,
                          event_subdata_initialized)
    sub = subdata.SubData(event_ev_template, event_charge_template,
                          event_cp_config, loadvars_.event_module_update_completed,
                          event_copy_data, event_global_data_initialized, event_command_completed,
                          event_subdata_initialized, soc.event_vehicle_update_completed,
                          event_scheduled_charging_plan, event_time_charging_plan,
                          general_internal_chargepoint_handler.event_start,
                          general_internal_chargepoint_handler.event_stop,
                          event_jobs_running)
    comm = command.Command(event_command_completed)
    t_sub = Thread(target=sub.sub_topics, args=())
    t_set = Thread(target=set.set_data, args=())
    t_comm = Thread(target=comm.sub_commands, args=())
    t_internal_chargepoint = Thread(target=general_internal_chargepoint_handler.handler,
                                    args=(), name="Internal Chargepoint")
    if hasattr(rfid0, "input_device"):
        t_rfid0 = Thread(target=rfid0.loop, args=(), name="Internal Chargepoint")
        t_rfid0.start()
    if hasattr(rfid1, "input_device"):
        t_rfid1 = Thread(target=rfid1.loop, args=(), name="Internal Chargepoint")
        t_rfid1.start()

    t_sub.start()
    t_set.start()
    t_comm.start()
    t_internal_chargepoint.start()
    # Warten, damit subdata Zeit hat, alle Topics auf dem Broker zu empfangen.
    time.sleep(5)
    schedule_jobs()
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
