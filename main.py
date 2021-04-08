"""Starten der benötigten Prozesse
"""

import imp
import subprocess
from threading import Thread
import threading

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
    set = setdata.setData()
    sub = subdata.subData()
    ticker = threading.Event()

    log.setup_logger()
    
    t_sub = Thread(target=sub.sub_topics, args=())
    t_set = Thread(target=set.set_data, args=())

    pub.setup_connection()
    t_sub.start()
    t_set.start()

    seconds = 10
    while not ticker.wait(seconds-3):
        try:
            imp.reload(publishvars2)
            publishvars2.pub_settings()
            output = subprocess.run(["./loadvars.sh"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if output.stderr.decode('utf-8') != "":
                log.message_debug_log("error", str(output.stderr.decode('utf-8')))
            ticker.wait(3)
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
