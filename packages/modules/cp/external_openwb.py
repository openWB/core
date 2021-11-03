from ...algorithm import data
from ...helpermodules import log
from ...helpermodules import pub


def read_external_openwb(cp):
    try:
        ip_address = cp.data["config"]["connection_module"]["config"]["external_openwb"]["ip_address"]
        cp_num = cp.cp_num
        duo_num = cp.data["config"]["connection_module"]["config"]["external_openwb"]["chargepoint"]
        try:
            with open('/var/www/html/openWB/ramdisk/ipaddress', 'r') as f:
                myipaddress = f.readline().replace("\n","")
        except:
            myipaddress = "192.168.193.5"
        pub.pub_single("openWB/set/isss/heartbeat", 0, hostname=ip_address)
        pub.pub_single("openWB/set/isss/parentWB", myipaddress, hostname=ip_address, no_json = True)
        if (duo_num == 2):
            pub.pub_single("openWB/set/isss/parentCPlp2", str(cp_num), hostname=ip_address)
            _check_duo_virtual_counter(cp)
        else:
            pub.pub_single("openWB/set/isss/parentCPlp1", str(cp_num), hostname=ip_address)
    except Exception as e:
        log.exception_logging(e)


def write_external_openwb(ip_address, num, current):
    try:
        # Zweiter LP der Duo
        if num == 2:
            pub.pub_single("openWB/set/isss/Lp2Current", current, hostname=ip_address)
        else:
            pub.pub_single("openWB/set/isss/Current", current, hostname=ip_address)
    except Exception as e:
        log.exception_logging(e)


def _check_duo_virtual_counter(cp):
    """ prüfen, ob es einen virtuellen Zähler gibt, an dem nur der erste und zweite Duo-Ladepunkt hängen. (Loadsharing)
    Wenn nein, wird ein solcher virtueller Zähler erstellt und in die Zählerhierarchie eingefügt.

    Parameter
    ---------
    cp: Dict
        Dict des zweiten Duo-Ladepunkts
    """
    try:
        # Zähler im Zweig der Duo
        counters = data.data.counter_data["all"].get_counters_to_check(cp)
        # virtuelle Zähler filtern
        for counter in counters:
            if data.data.counter_data[counter].data["config"]["selected"] == "virtual":
                # prüfen, dass nur eine weitere WB dran hängt
                connected_cps = data.data.counter_data["all"].get_chargepoints_of_counter(counter)
                if len(connected_cps) == 2:
                    # prüfen, ob das der erste Duo-Ladepunkt ist
                    if (data.data.cp_data[connected_cps[0]].data["config"]["connection_module"]["config"]["external_openwb"]["ip_address"] ==
                            data.data.cp_data[connected_cps[1]].data["config"]["connection_module"]["config"]["external_openwb"]["ip_address"]):
                        break
        else:
            # Es wurde kein virtueller Zähler gefunden.
            # Anderen Ladepunkt finden
            for chargepoint in data.data.cp_data:
                if "cp" in chargepoint:
                    if data.data.cp_data[chargepoint].data["config"]["connection_module"]["selected"] == "external_openwb":
                        if ((data.data.cp_data[chargepoint].data["config"]["connection_module"]["config"]["external_openwb"]["ip_address"] ==
                                cp.data["config"]["connection_module"]["config"]["external_openwb"]["ip_address"]) and
                                (data.data.cp_data[chargepoint].data["config"]["connection_module"]["config"]["external_openwb"]["chargepoint"] !=
                                 cp.data["config"]["connection_module"]["config"]["external_openwb"]["chargepoint"])):
                            connected_cps = ["cp"+str(cp.cp_num), "cp"+str(data.data.cp_data[chargepoint].cp_num)]
                            break
            else:
                log.message_debug_log("error", "Es konnte kein zweiter Ladepunkt für die openWB-Duo an Ladepunkt "+str(cp.cp_num)+" gefunden werden.")
            index = 1
            for index in range(0, 2000):
                for counter in data.data.counter_data:
                    if "counter" in counter:
                        if data.data.counter_data[counter].counter_num == index:
                            break
                else:
                    # Die Nummer gibts noch nicht.
                    break
                index = index + 1
            pub.pub("openWB/set/counter/"+str(index)+"/config", {"max_current": [16, 16, 16], "selected": "virtual"})

            # Hierarchie erweitern
            ret = data.data.counter_data["all"].hierarchy_add_item_aside("counter"+str(index), "cp"+str(cp.cp_num))
            if ret == False:
                log.message_debug_log("error", "counter"+str(index)+" konnte nicht auf der Ebene von cp"+str(cp.cp_num)+" in die Zaehlerhierarchie eingefuegt werden.")
                return
            ret = data.data.counter_data["all"].hierarchy_remove_item("cp"+str(data.data.cp_data[connected_cps[0]].cp_num), keep_children=False)
            if ret == False:
                log.message_debug_log("error", "cp"+str(data.data.cp_data[connected_cps[0]].cp_num)+" konnte nicht aus der Zaehlerhierarchie geloescht werden.")
                return
            ret = data.data.counter_data["all"].hierarchy_remove_item("cp"+str(data.data.cp_data[connected_cps[1]].cp_num), keep_children=False)
            if ret == False:
                log.message_debug_log("error", "cp"+str(data.data.cp_data[connected_cps[1]].cp_num)+" konnte nicht aus der Zaehlerhierarchie geloescht werden.")
                return
            ret = data.data.counter_data["all"].hierarchy_add_item_below("cp"+str(data.data.cp_data[connected_cps[0]].cp_num), "counter"+str(index))
            if ret == False:
                log.message_debug_log("error", "cp"+str(cp.cp_num)+" konnte nicht unter der Ebene von counter"+str(index)+" in die Zaehlerhierarchie eingefuegt werden.")
                return
            ret = data.data.counter_data["all"].hierarchy_add_item_below("cp"+str(data.data.cp_data[connected_cps[1]].cp_num), "counter"+str(index))
            if ret == False:
                log.message_debug_log("error", "cp"+str(cp.cp_num)+" konnte nicht unter der Ebene von counter"+str(index)+" in die Zaehlerhierarchie eingefuegt werden.")
                return
    except Exception as e:
        log.exception_logging(e)
