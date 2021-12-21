#!/usr/bin/env python3
"""Starten der benötigten Prozesse
"""
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
from helpermodules import publishvars2
from helpermodules import measurement_log
from helpermodules.log import MainLogger, cleanup_logfiles
from helpermodules import command
from control import prepare
from control import data
from control import process
from control import algorithm
from helpermodules.system import exit_after


class HandlerAlgorithm:
    def __init__(self):
        self.heartbeat = False
        self.interval_counter = 1
        self.current_day = None

    def handler10Sec(self):
        """ führt den Algorithmus durch.
        """
        try:
            # Beim ersten Durchlauf wird in jedem Fall eine Exception geworfen, da die Daten erstmalig ins data-Modul
            # kopiert werden müssen.
            try:
                exit_time = data.data.general_data["general"].data["control_interval"]

                @exit_after(exit_time)
                def handler_with_control_interval():
                    if (data.data.general_data["general"].data["control_interval"]
                            / 10) == self.interval_counter:
                        # Mit aktuellen Einstellungen arbeiten.
                        prep.copy_system_data()
                        MainLogger().set_log_level(data.data.system_data["system"].data["debug_level"])
                        loadvars.get_hardware_values()
                        # Virtuelle Module ermitteln die Werte rechnerisch auf Bais der Messwerte anderer Module.
                        # Daher können sie erst die Werte ermitteln, wenn die physischen Module ihre Werte ermittelt
                        # haben. Würde man allle Module parallel abfragen, wären die virtuellen Module immer einen
                        # Zyklus hinterher.
                        prep.copy_counter_data()
                        loadvars.get_virtual_values()
                        # Kurz warten, damit alle Topics von setdata und subdata verarbeitet werden könnnen.
                        time.sleep(0.5)
                        prep.copy_data()
                        self.heartbeat = True
                        if data.data.system_data["system"].data["perform_update"]:
                            data.data.system_data["system"].perform_update()
                            return
                        elif data.data.system_data["system"].data[
                                "update_in_progress"]:
                            MainLogger().info(
                                "Regelung pausiert, da ein Update durchgefuehrt wird."
                            )
                            return
                        prep.setup_algorithm()
                        control.calc_current()
                        proc.process_algorithm_results()
                        data.data.graph_data["graph"].pub_graph_data()
                        self.interval_counter = 1
                    else:
                        self.interval_counter = self.interval_counter + 1
                handler_with_control_interval()
            except Exception:
                @exit_after(10)
                def handler_without_contronl_interval():
                    # Wenn kein Regelintervall bekannt ist, alle 10s regeln.
                    prep.copy_system_data()
                    loadvars.get_hardware_values()
                    prep.copy_counter_data()
                    loadvars.get_virtual_values()
                    self.heartbeat = True
                    # Kurz warten, damit alle Topics von setdata und subdata verarbeitet werden könnnen.
                    time.sleep(0.3)
                    prep.copy_data()
                    prep.setup_algorithm()
                    control.calc_current()
                    proc.process_algorithm_results()
                    data.data.graph_data["graph"].pub_graph_data()
                handler_without_contronl_interval()
        except Exception:
            MainLogger().exception("Fehler im Main-Modul")

    @exit_after(10)
    def handler5Min(self):
        """ Handler, der alle 5 Minuten aufgerufen wird und die Heartbeats der Threads überprüft und die Aufgaben
        ausführt, die nur alle 5 Minuten ausgeführt werden müssen.
        """
        try:
            MainLogger().debug("5 Minuten Handler ausführen.")
            if not sub.heartbeat:
                MainLogger().error("Heartbeat fuer Subdata nicht zurueckgesetzt.")
                sub.disconnect()
                Thread(target=sub.sub_topics, args=()).start()
            else:
                sub.heartbeat = False

            if not set.heartbeat:
                MainLogger().error("Heartbeat fuer Setdata nicht zurueckgesetzt.")
                set.disconnect()
                Thread(target=set.set_data, args=()).start()
            else:
                set.heartbeat = False

            cleanup_logfiles()
            measurement_log.save_log("daily")
            measurement_log.update_daily_yields()
            # Wenn ein neuer Tag ist, Monatswerte schreiben.
            day = timecheck.create_timestamp_YYYYMMDD()[-2:]
            if self.current_day != day:
                self.current_day = day
                measurement_log.save_log("monthly")
            data.data.general_data["general"].grid_protection()
            data.data.optional_data["optional"].et_get_prices()
            data.data.counter_data["all"].calc_daily_yield_home_consumption()
        except Exception:
            MainLogger().exception("Fehler im Main-Modul")


def repeated_handler_call():
    """https://stackoverflow.com/questions/474528/
    what-is-the-best-way-to-repeatedly-execute-a-function-every-x-seconds/25251804#25251804
    """
    delay = 10
    timer_5min = 0
    next_time = time.time() + delay
    while True:
        time.sleep(max(0, next_time - time.time()))
        try:
            if timer_5min == 300:
                handler.handler5Min()
                timer_5min = 0
            else:
                timer_5min += 10
            handler.handler10Sec()
        except KeyboardInterrupt:
            MainLogger().critical("Asuführung durch exit_after gestoppt: "+traceback.format_exc())
        except Exception:
            MainLogger().exception("Fehler im Main-Modul")
        # skip tasks if we are behind schedule:
        next_time += (time.time() - next_time) // delay * delay + delay


try:
    # Regelung erst starten, wenn atreboot.sh fertig ist.
    MainLogger().debug("Warten auf das Ende des Boot-Prozesses")
    while os.path.isfile(os.path.dirname(os.path.abspath(__file__)) + "/../ramdisk/bootdone") is False:
        time.sleep(1)
    MainLogger().debug("Boot-Prozess abgeschlossen")

    data.data_init()
    update_config.UpdateConfig().update()
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
    set = setdata.SetData(event_ev_template, event_charge_template,
                          event_cp_config)
    sub = subdata.SubData(event_ev_template, event_charge_template,
                          event_cp_config)
    comm = command.Command()
    t_sub = Thread(target=sub.sub_topics, args=())
    t_set = Thread(target=set.set_data, args=())
    t_comm = Thread(target=comm.sub_commands, args=())

    t_sub.start()
    t_set.start()
    t_comm.start()

    publishvars2.pub_settings()
    configuration.pub_configurable()

    # blocking
    repeated_handler_call()
except Exception:
    MainLogger().exception("Fehler im Main-Modul")
