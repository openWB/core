"""Starten der benötigten Prozesse
"""

from threading import Thread
import threading

import algorithm
import charge
import data
import log
import prepare
import pub
import setdata
import subdata

def main():
    # pub_data=pubdata.pullModules()
    char = charge.charge()
    control = algorithm.control()
    prep = prepare.prepare()
    set = setdata.setData()
    sub = subdata.subData()
    ticker = threading.Event()

    log.setup_logger()
    
    t_sub = Thread(target=sub.sub_topics, args=())
    t_set = Thread(target=set.set_data, args=())

    pub.setup_connection()
    t_sub.start()
    t_set.start()

    seconds = 3
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
