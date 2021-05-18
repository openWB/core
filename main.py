"""Starten der benötigten Prozesse
"""

import imp
import subprocess
from threading import Thread
import threading
import time

import algorithm
import charge
import data
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
    lock_ev_template = threading.Lock()
    lock_charge_template = threading.Lock()
    set = setdata.setData(lock_ev_template, lock_charge_template)
    sub = subdata.subData(lock_ev_template, lock_charge_template)
    ticker = threading.Event()

    log.setup_logger()
    
    
    t_sub = Thread(target=sub.sub_topics, args=())
    t_set = Thread(target=set.set_data, args=())

    pub.setup_connection()
    t_sub.start()
    t_set.start()

    publishvars2.pub_settings()

    seconds = 10
    while not ticker.wait(seconds):
        try:
            prep.setup_algorithm()
            control.calc_current()
            char.start_charging()
            if "general" in sub.general_data:
                if "control_interval" in sub.general_data["general"].data:
                    seconds = sub.general_data["general"].data["control_interval"]
                else:
                    seconds = 10
            else:
                seconds = 10
        except Exception as e:
            log.exception_logging(e)


main()
