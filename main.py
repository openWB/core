"""Starten der benötigten Prozesse
"""

from threading import Thread
import threading
import traceback

import data
import log
import prepare
import pub
import subdata

def main():
    # pub_data=pubdata.pullModules()
    log.setup_logger()
    sub = subdata.subData()
    ticker = threading.Event()
    prep = prepare.prepare()
    t = Thread(target=sub.sub_topics, args=())

    pub.setup_connection()
    t.start()
    try:
        seconds = 10
        while not ticker.wait(seconds):
            prep.setup_algorithm()
            if "general" in sub.general_data:
                if "control_interval" in sub.general_data["general"].data:
                    seconds = sub.general_data["general"].data["control_interval"]
                else:
                    seconds = 10
            else:
                seconds = 10
    except Exception:
        traceback.print_exc(limit=-1)

main()
