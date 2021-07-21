#!/usr/bin/env python3
"""Starten der benötigten Prozesse
"""

from threading import Thread
import threading
import time

from packages.algorithm import algorithm
from packages.algorithm import charge
from packages.algorithm import daily_log
from packages.algorithm import data
from packages.helpermodules import log
from packages.algorithm import prepare
from packages.helpermodules import pub
from packages.helpermodules import publishvars2
from packages.helpermodules import setdata
from packages.helpermodules import subdata
from packages.modules import loadvars

class HandlerAlgorithm():
    def __init__(self):
        self.heartbeat = False

    def handler10Sec(self):
        """ führt den Algorithmus durch.
        """
        try:
            vars.get_values()
            self.heartbeat = True
            prep.setup_algorithm()
            control.calc_current()
            char.start_charging()
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

def handler5Min():
    """ Handler, der alle 5 Minuten aufgerufen wird und die Heartbeats der Threads überprüft und die Aufgaben ausführt, die nur alle 5 Minuten ausgeführt werden müssen.
    """
    if handler.heartbeat == False:
        pass
    else:
        handler.hartbeat = False

    if sub.heartbeat == False:
        pass
    else:
        sub.hartbeat = False

    if set.heartbeat == False:
        pass
    else:
        set.hartbeat = False

    daily_log.save_daily_log()
    data.data.general_data["general"].grid_protection()
    data.data.optional_data["optional"].et_get_prices()

try:
    data.data_init()
    char = charge.charge()
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
    rt = RepeatedTimer(300, handler5Min)
    rt2 = RepeatedTimer(10, handler.handler10Sec)

    publishvars2.pub_settings()
except Exception as e:
    log.exception_logging(e)