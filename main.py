#!/bin/python3
"""Starten der benötigten Prozesse
"""

from threading import Thread
import threading

import algorithm
import charge
import log
import prepare
import pub
import publishvars2
import setdata
import subdata

def main():
    # pub_data=pubdata.pullModules()
    char = charge.charge()
    control = algorithm.control()
    prep = prepare.prepare()
    loadvarsdone = threading.Event()
    lock_ev_template = threading.Lock()
    lock_charge_template = threading.Lock()
    set = setdata.setData(lock_ev_template, lock_charge_template)
    sub = subdata.subData(lock_ev_template, lock_charge_template, loadvarsdone)

    log.setup_logger()
    
    
    t_sub = Thread(target=sub.sub_topics, args=())
    t_set = Thread(target=set.set_data, args=())

    pub.setup_connection()
    t_sub.start()
    t_set.start()

    publishvars2.pub_settings()

    while loadvarsdone.wait():
        loadvarsdone.clear()
        try:
            prep.setup_algorithm()
            control.calc_current()
            char.start_charging()
        except Exception as e:
            log.exception_logging(e)


main()
