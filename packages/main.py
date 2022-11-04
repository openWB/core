#!/usr/bin/env python3
"""Starten der benötigten Prozesse
"""
import logging
import os
import time
import threading
import traceback
from threading import Thread

from modules import loadvars
from modules import configuration
from helpermodules import update_config
from helpermodules import timecheck
from helpermodules import subdata
from helpermodules import setdata
from helpermodules import measurement_log
from helpermodules import logger
from helpermodules.logger import cleanup_logfiles
from helpermodules import command
from control import prepare
from control import data
from control import process
from control import algorithm
from helpermodules.system import exit_after
from modules import update_soc

logger.setup_logging()
log = logging.getLogger()


class HandlerAlgorithm:
    def __init__(self):
        self.heartbeat = False
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

            if not soc.heartbeat:
                log.error("Heartbeat für SoC-Abfrage nicht zurückgesetzt.")
            else:
                soc.heartbeat = False

            cleanup_logfiles()
            measurement_log.measurement_log_daily()
            # Wenn ein neuer Tag ist, Monatswerte schreiben.
            day = timecheck.create_timestamp_YYYYMMDD()[-2:]
            if self.current_day != day:
                self.current_day = day
                measurement_log.save_log("monthly")
            data.data.general_data.grid_protection()
            data.data.optional_data.et_get_prices()
            data.data.system_data["system"].update_ip_address()
        except Exception:
            log.exception("Fehler im Main-Modul")


def repeated_handler_call():
    """https://stackoverflow.com/questions/474528/
    what-is-the-best-way-to-repeatedly-execute-a-function-every-x-seconds/25251804#25251804
    """
    delay = 10
    timer_5min = 0
    next_time = time.time() + delay
    while True:
        try:
            if timer_5min >= 290:
                handler.handler5Min()
                timer_5min = 0
            else:
                timer_5min += 10
            handler.handler10Sec()
        except KeyboardInterrupt:
            log.critical("Ausführung durch exit_after gestoppt: "+traceback.format_exc())
        except Exception:
            log.exception("Fehler im Main-Modul")
        # skip tasks if we are behind schedule:
        next_time += (time.time() - next_time) // delay * delay + delay
        time.sleep(max(0, next_time - time.time()))


try:
    # Regelung erst starten, wenn atreboot.sh fertig ist.
    log.debug("Warten auf das Ende des Boot-Prozesses")
    while os.path.isfile(os.path.dirname(os.path.abspath(__file__)) + "/../ramdisk/bootdone") is False:
        time.sleep(1)
    log.debug("Boot-Prozess abgeschlossen")

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
    prep = prepare.Prepare()
    set = setdata.SetData(event_ev_template, event_charge_template,
                          event_cp_config)
    sub = subdata.SubData(event_ev_template, event_charge_template,
                          event_cp_config, loadvars_.event_module_update_completed,
                          event_copy_data, event_global_data_initialized)
    comm = command.Command()
    soc = update_soc.UpdateSoc()
    t_sub = Thread(target=sub.sub_topics, args=())
    t_set = Thread(target=set.set_data, args=())
    t_comm = Thread(target=comm.sub_commands, args=())
    t_soc = Thread(target=soc.update, args=())

    t_sub.start()
    t_set.start()
    t_comm.start()
    t_soc.start()
except Exception:
    log.exception("Fehler im Main-Modul")
# Warten, damit subdata Zeit hat, alle Topics auf dem Broker zu empfangen.
time.sleep(5)
# blocking
repeated_handler_call()
