#!/usr/bin/env python3
"""Starten der benötigten Prozesse
"""

from threading import Thread
import threading
import time

from packages.algorithm import algorithm
from packages.algorithm import process
from packages.algorithm import data
from packages.algorithm import prepare
from packages.helpermodules import defaults
from packages.helpermodules import graph
from packages.helpermodules import log
from packages.helpermodules import measurement_log
from packages.helpermodules import pub
from packages.helpermodules import publishvars2
from packages.helpermodules import setdata
from packages.helpermodules import subdata
from packages.helpermodules import timecheck
from packages.modules import loadvars

# Wenn debug True ist, wird der 10s Handler nicht durch den Timer-Thread gesteuert, sondern macht ein 10s Sleep am Ende, da sonst beim Pausieren immer mehr Threads im Hintergrund auflaufen.
debug = True

class HandlerAlgorithm():
    def __init__(self):
        self.heartbeat = False
        self.interval_counter = 1
        self.current_day = None

    def handler10Sec(self):
        """ führt den Algorithmus durch.
        """
        try:
            try:
                if (data.data.general_data["general"].data["control_interval"] / 10) == self.interval_counter:
                    # Mit aktuellen Einstellungen arbeiten.
                    log.message_debug_log("info", " Start copy_data 1")
                    prep.copy_data()
                    log.message_debug_log("info", " Stop copy_data 1")
                    vars.get_values()
                    # Virtuelle Module ermitteln die Werte rechnerisch auf Bais der Messwerte anderer Module. 
                    # Daher können sie erst die Werte ermitteln, wenn die physischen Module ihre Werte ermittelt haben.
                    # Würde man allle Module parallel abfragen, wären die virtuellen Module immer einen Zyklus hinterher.
                    log.message_debug_log("info", " Start copy_data 2")
                    prep.copy_data()
                    log.message_debug_log("info", " Stop copy_data 2")
                    vars.get_virtual_values()
                    # Kurz warten, damit alle Topics von setdata und subdata verarbeitet werden könnnen.
                    time.sleep(1)
                    log.message_debug_log("info", " Start copy_data 3")
                    prep.copy_data()
                    log.message_debug_log("info", " Stop copy_data 3")
                    self.heartbeat = True
                    prep.setup_algorithm()
                    control.calc_current()
                    proc.process_algorithm_results()
                    graph.pub_graph_data()
                    self.interval_counter = 1
                else:
                    self.interval_counter = self.interval_counter + 1
            except:
                # Wenn kein Regelintervall bekannt ist, alle 10s regeln.
                prep.copy_data()
                vars.get_values()
                prep.copy_data()
                vars.get_virtual_values()
                self.heartbeat = True
                # Kurz warten, damit alle Topics von setdata und subdata verarbeitet werden könnnen.
                time.sleep(0.3)
                prep.copy_data()
                prep.setup_algorithm()
                control.calc_current()
                proc.process_algorithm_results()
                graph.pub_graph_data()
        except Exception as e:
            log.exception_logging(e)
    
    def handler5Min(self):
        """ Handler, der alle 5 Minuten aufgerufen wird und die Heartbeats der Threads überprüft und die Aufgaben ausführt, die nur alle 5 Minuten ausgeführt werden müssen.
        """
        try:
            if self.heartbeat == False:
                pass
            else:
                self.hartbeat = False

            if sub.heartbeat == False:
                pass
            else:
                sub.hartbeat = False

            if set.heartbeat == False:
                pass
            else:
                set.hartbeat = False

            log.cleanup_logfiles()
            measurement_log.save_log("daily")
            measurement_log.update_daily_yields()
            #Wenn ein neuer Tag ist, Monatswerte schreiben.
            day = timecheck.create_timestamp_YYYYMMDD()[-2:]
            if self.current_day != day:
                self.current_day = day
                measurement_log.save_log("monthly")
            data.data.general_data["general"].grid_protection()
            data.data.optional_data["optional"].et_get_prices()
            data.data.cp_data["all"].check_all_modbus_evse_connections()
            data.data.counter_data["all"].calc_daily_yield_home_consumption()
        except Exception as e:
            log.exception_logging(e)

class RepeatedTimer(object):
    """ führt alle x Sekunden einen Thread aus, unabhängig davon, ob sich der Thread bei der vorherigen Ausführung aufgehängt etc hat.
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
            self._timer = threading.Timer(self.next_call - time.time(), self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False

try:
    data.data_init()
    proc = process.process()
    control = algorithm.control()
    handler = HandlerAlgorithm()
    vars = loadvars.loadvars()
    prep = prepare.prepare()
    loadvarsdone = threading.Event()
    event_ev_template = threading.Event()
    event_ev_template.set()
    event_charge_template = threading.Event()
    event_charge_template.set()
    set = setdata.setData(event_ev_template, event_charge_template)
    sub = subdata.subData(event_ev_template, event_charge_template, loadvarsdone)
    t_sub = Thread(target=sub.sub_topics, args=())
    t_set = Thread(target=set.set_data, args=())


    log.setup_logger()
    pub.setup_connection()
    t_sub.start()
    t_set.start()
    rt = RepeatedTimer(300, handler.handler5Min)
    if debug == False:
        rt2 = RepeatedTimer(10, handler.handler10Sec)

    publishvars2.pub_settings()
    defaults.pub_defaults()

    if debug == True:
        while True:
            time.sleep(10)
            handler.handler10Sec()
except Exception as e:
    log.exception_logging(e)