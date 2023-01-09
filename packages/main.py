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
                    data.data.graph_data["graph"].pub_graph_data()
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

            cleanup_logfiles()
            measurement_log.measurement_log_daily()
            data.data.general_data.grid_protection()
            data.data.optional_data.et_get_prices()
            data.data.system_data["system"].update_ip_address()
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
    [schedule.every().minute.at(f":{i:02d}").do(handler.handler10Sec) for i in range(0, 60, 10)]
    [schedule.every().minute.at(f":{i:02d}").do(soc.update) for i in range(0, 60, 10)]
    [schedule.every().hour.at(f":{i:02d}").do(handler.handler5Min) for i in range(0, 60, 5)]
    schedule.every().day.at("00:00:00").do(handler.handler_midnight)


try:
    log.debug("Start openWB2.service")
    loadvars_ = loadvars.Loadvars()
    data.data_init(loadvars_.event_module_update_completed)
    update_config.UpdateConfig().update()
    configuration.pub_configurable()
    proc = process.Process()
    control = algorithm.Algorithm()
    handler = HandlerAlgorithm()
    prep = prepare.Prepare()
    event_ev_template = threading.Event()
    event_ev_template.set()
    event_charge_template = threading.Event()
    event_charge_template.set()
    event_cp_config = threading.Event()
    event_cp_config.set()
    event_copy_data = threading.Event()  # set: Kopieren abgeschlossen, reset: es wird kopiert
    event_copy_data.set()
    event_global_data_initialized = threading.Event()
    event_command_completed = threading.Event()
    event_command_completed.set()
    event_subdata_initialized = threading.Event()
    prep = prepare.Prepare()
    soc = update_soc.UpdateSoc()
    set = setdata.SetData(event_ev_template, event_charge_template,
                          event_cp_config, event_subdata_initialized)
    sub = subdata.SubData(event_ev_template, event_charge_template,
                          event_cp_config, loadvars_.event_module_update_completed,
                          event_copy_data, event_global_data_initialized, event_command_completed,
                          event_subdata_initialized, soc.event_vehicle_update_completed)
    comm = command.Command(event_command_completed)
    t_sub = Thread(target=sub.sub_topics, args=())
    t_set = Thread(target=set.set_data, args=())
    t_comm = Thread(target=comm.sub_commands, args=())

    t_sub.start()
    t_set.start()
    t_comm.start()
    # Warten, damit subdata Zeit hat, alle Topics auf dem Broker zu empfangen.
    time.sleep(5)
    schedule_jobs()
except Exception:
    log.exception("Fehler im Main-Modul")

while True:
    try:
        schedule.run_pending()
        time.sleep(1)
    except Exception:
        log.exception("Fehler im Main-Modul")
