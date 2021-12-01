#!/usr/bin/env python3
"""Starten der benötigten Prozesse
"""
import os
import time
import threading
from threading import Thread

from modules import loadvars
from modules import configuration
from helpermodules import update_config
from helpermodules import timecheck
from helpermodules import subdata
from helpermodules import setdata
from helpermodules import publishvars2
from helpermodules import measurement_log
from helpermodules import log
from helpermodules import command
from control import prepare
from control import data
from control import process
from control import algorithm


# Wenn debug True ist, wird der 10s Handler nicht durch den Timer-Thread gesteuert, sondern macht ein 10s Sleep am
# Ende, da sonst beim Pausieren immer mehr Threads im Hintergrund auflaufen.
debug = False


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
                if (data.data.general_data["general"].data["control_interval"]
                        / 10) == self.interval_counter:
                    # Mit aktuellen Einstellungen arbeiten.
                    log.MainLogger().debug(" Start copy_data 1")
                    prep.copy_system_data()
                    log.MainLogger().set_log_level(data.data.system_data["system"].data["debug_level"])
                    log.MainLogger().debug(" Stop copy_data 1")
                    vars.get_values()
                    # Virtuelle Module ermitteln die Werte rechnerisch auf Bais der Messwerte anderer Module.
                    # Daher können sie erst die Werte ermitteln, wenn die physischen Module ihre Werte ermittelt haben.
                    # Würde man allle Module parallel abfragen, wären die virtuellen Module immer einen Zyklus
                    # hinterher.
                    log.MainLogger().debug(" Start copy_data 2")
                    prep.copy_counter_data()
                    log.MainLogger().debug(" Stop copy_data 2")
                    vars.get_virtual_values()
                    # Kurz warten, damit alle Topics von setdata und subdata verarbeitet werden könnnen.
                    time.sleep(0.5)
                    log.MainLogger().debug(" Start copy_data 3")
                    prep.copy_data()
                    log.MainLogger().debug(" Stop copy_data 3")
                    self.heartbeat = True
                    if data.data.system_data["system"].data["perform_update"]:
                        data.data.system_data["system"].perform_update()
                        return
                    elif data.data.system_data["system"].data[
                            "update_in_progress"]:
                        log.MainLogger().info(
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
            except Exception:
                # Wenn kein Regelintervall bekannt ist, alle 10s regeln.
                prep.copy_system_data()
                vars.get_values()
                prep.copy_counter_data()
                vars.get_virtual_values()
                self.heartbeat = True
                # Kurz warten, damit alle Topics von setdata und subdata verarbeitet werden könnnen.
                time.sleep(0.3)
                prep.copy_data()
                prep.setup_algorithm()
                control.calc_current()
                proc.process_algorithm_results()
                data.data.graph_data["graph"].pub_graph_data()
        except Exception:
            log.MainLogger().exception("Fehler im Main-Modul")

    def handler5Min(self):
        """ Handler, der alle 5 Minuten aufgerufen wird und die Heartbeats der Threads überprüft und die Aufgaben
        ausführt, die nur alle 5 Minuten ausgeführt werden müssen.
        """
        try:
            log.MainLogger().debug("5 Minuten Handler ausführen.")
            if not self.heartbeat:
                log.MainLogger().error(
                    "Heartbeat fuer Algorithmus nicht zurueckgesetzt.")
            else:
                self.hartbeat = False

            if not sub.heartbeat:
                log.MainLogger().error(
                    "Heartbeat fuer Subdata nicht zurueckgesetzt.")
            else:
                sub.hartbeat = False

            if not set.heartbeat:
                log.MainLogger().error(
                    "Heartbeat fuer Setdata nicht zurueckgesetzt.")
            else:
                set.hartbeat = False

            log.cleanup_logfiles()
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
            log.MainLogger().exception("Fehler im Main-Modul")


class RepeatedTimer(object):
    """ führt alle x Sekunden einen Thread aus, unabhängig davon, ob sich der Thread bei der vorherigen Ausführung
    aufgehängt etc hat.
    https://stackoverflow.com/a/40965385
    """

    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.next_call = time.time()
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self.next_call += self.interval
            self._timer = threading.Timer(self.next_call - time.time(),
                                          self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False


try:
    # Regelung erst starten, wenn atreboot.sh fertig ist.
    log.MainLogger().debug("Warten auf das Ende des Boot-Prozesses")
    while os.path.isfile(os.path.dirname(os.path.abspath(__file__)) + "/../ramdisk/bootdone") is False:
        time.sleep(1)
    log.MainLogger().debug("Boot-Prozess abgeschlossen")

    data.data_init()
    update_config.UpdateConfig().update()
    proc = process.process()
    control = algorithm.control()
    handler = HandlerAlgorithm()
    vars = loadvars.loadvars()
    prep = prepare.prepare()
    event_ev_template = threading.Event()
    event_ev_template.set()
    event_charge_template = threading.Event()
    event_charge_template.set()
    event_cp_config = threading.Event()
    event_cp_config.set()
    set = setdata.setData(event_ev_template, event_charge_template,
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

    rt = RepeatedTimer(300, handler.handler5Min)
    if not debug:
        rt2 = RepeatedTimer(10, handler.handler10Sec)
    else:
        while True:
            time.sleep(10)
            handler.handler10Sec()
except Exception:
    log.MainLogger().exception("Fehler im Main-Modul")
