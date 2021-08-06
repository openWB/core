from ...helpermodules import pub

def mqtt_state(cp):
    cp_num = cp.cp_num
    pub.pub("openWB/set/chargepoint/"+str(cp_num)+"/get/fault_state", 0)
    pub.pub("openWB/set/chargepoint/"+str(cp_num)+"/get/fault_str", "Kein Fehler")