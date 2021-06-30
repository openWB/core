#!/usr/bin/env python3
"""Starten der benötigten Prozesse
"""

from threading import Thread
import threading
import time

import algorithm
import charge
import daily_log
import log
import prepare
import pub
import publishvars2
import setdata
import subdata

def handler(loadvarsdone):
    """ führt den Algorithmus durch.

    Parameter
    ---------
    loadvardone: event
        Event, das angibt, ob die loadvars abgearbeitet wurde.
    """
    try:
        while loadvarsdone.wait():
            loadvarsdone.clear()
            try:
                prep.setup_algorithm()
                control.calc_current()
                char.start_charging()
            except Exception as e:
                log.exception_logging(e)
    except Exception as e:
        log.exception_logging(e)

class RepeatedTimer(object):
    """ https://stackoverflow.com/a/40965385
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
    char = charge.charge()
    control = algorithm.control()
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
    t_handler = Thread(target=handler, args=(loadvarsdone,))


    log.setup_logger()
    pub.setup_connection()
    t_sub.start()
    t_set.start()
    t_handler.start()
    rt = RepeatedTimer(60, daily_log.save_daily_log)

    publishvars2.pub_settings()
except Exception as e:
    log.exception_logging(e)