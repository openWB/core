"""Starten der benötigten Prozesse
"""

import prepare
import pubdata
import subdata

def main(self):
    prep=prepare.prepare()
    #pub=pubdata.pullModules()
    sub=subdata.mqtt()
    
    # timer-thread prep
    #thread sub
    #timer-thread pub

