""" Virtueller Zähler
Der Zähler addiert die Ladeleistungen der angegebenen Ladepunkte und wird im Algorithmus wie ein physischer Zähler behandelt.
"""

from ...algorithm import data
from ...helpermodules import log
from ...helpermodules import pub
from ...helpermodules import simcount


def read_virtual_counter(counter):
    try:
        # "Angeschlossene" Ladepunkte ermitteln
        counter_name = "counter"+str(counter.counter_num)
        chargepoints = data.data.counter_data["all"].get_chargepionts_of_counter(counter_name)
        # Ladeleistungen, Ströme addieren
        current = [0]*3
        power_all = 0
        for cp in chargepoints:
            chargepoint = data.data.cp_data[cp]
            # Phase 1 LP = Phase 1 EVU
            if chargepoint.data["config"]["phase_1"] == 1:
                current[0] = current[0] + chargepoint.data["get"]["current"][0]
                current[1] = current[1] + chargepoint.data["get"]["current"][1]
                current[2] = current[2] + chargepoint.data["get"]["current"][2]
            # Phase 1 LP = Phase 2 EVU
            elif chargepoint.data["config"]["phase_1"] == 2:
                current[0] = current[0] + chargepoint.data["get"]["current"][1]
                current[1] = current[1] + chargepoint.data["get"]["current"][2]
                current[2] = current[2] + chargepoint.data["get"]["current"][0]
            # Phase 1 LP = Phase 3 EVU
            elif chargepoint.data["config"]["phase_1"] == 3:
                current[0] = current[0] + chargepoint.data["get"]["current"][2]
                current[1] = current[1] + chargepoint.data["get"]["current"][0]
                current[2] = current[2] + chargepoint.data["get"]["current"][1]
            else:
                log.message_debug_log("error", "Fuer den virtuellen Zaehler muss der Anschluss der Phasen vom Ladepunkt "+str(chargepoint.cp_num)+" an die Phasen der EVU angegeben werden.")
            power_all = power_all + chargepoint.data["get"]["power_all"]
            power_phase = [230*c for c in current]
        # Werte publishen
        pub.pub("openWB/set/counter/"+str(counter.counter_num)+"/get/current", current)
        pub.pub("openWB/set/counter/"+str(counter.counter_num)+"/get/voltage", [230, 230, 230])
        pub.pub("openWB/set/counter/"+str(counter.counter_num)+"/get/power_phase", power_phase)
        pub.pub("openWB/set/counter/"+str(counter.counter_num)+"/get/power_all", power_all)
        # Import Export simulieren
        simcount.sim_count(power_all, "openWB/set/counter/"+str(counter.counter_num)+"/", counter.data["set"])
    except Exception as e:
        log.exception_logging(e)
