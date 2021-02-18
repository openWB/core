"""Starten der benötigten Prozesse
"""

from threading import Thread    
import threading

import data
import prepare
import subdata

def main():
    #pub=pubdata.pullModules()
    sub=subdata.subData()
    ticker = threading.Event()
    prep=prepare.prepare()
    t = Thread(target=sub.sub_topics, args=())

    t.start()

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

main()