"""Starten der benötigten Prozesse
"""

from threading import Thread

import subdata

def main():
    #pub=pubdata.pullModules()
    sub=subdata.subData()
    t = Thread(target=sub.sub_topics, args=())

    t.start()
    #timer-thread pub

main()