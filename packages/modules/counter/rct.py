#!/usr/bin/python

import fnmatch

from ...helpermodules import pub
from ...helpermodules import simcount
from . import rct_lib

# Entry point with parameter check
def read_value(argv):
    ret_val = None
    rct_lib.init(argv)

    clientsocket = rct_lib.connect_to_server()
    if clientsocket is not None:
        fmt = '#0x{:08X} {:'+str(rct_lib.param_len)+'}'# {:'+str(rct_lib.desc_len)+'}:'
        for obj in rct_lib.id_tab:
            if rct_lib.search_id > 0 and obj.id != rct_lib.search_id:
                continue
            
            if rct_lib.search_name is not None and fnmatch.fnmatch(obj.name, rct_lib.search_name) == False:
                continue
            
            value = rct_lib.read(clientsocket, obj.id)
            if rct_lib.dbglog(fmt.format(obj.id, obj.name), value) == False:
                ret_val = value
        rct_lib.close(clientsocket)
    return ret_val

def read_rct(counter):
    counter_num = counter.counter_num
    wattbezug = int(read_value(counter.data["config"]["config"]["rct"]["ip_address"], name='g_sync.p_ac_sc_sum'))
    current1 = int(read_value(counter.data["config"]["config"]["rct"]["ip_address"], id='0x27BE51D9') / 230)
    current2 = int(read_value(counter.data["config"]["config"]["rct"]["ip_address"], id='0xF5584F90') / 230)
    current3 = int(read_value(counter.data["config"]["config"]["rct"]["ip_address"], id='0xB221BCFA') / 230)
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/current", [current1, current2, current3])
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_all", wattbezug)

    simcount.sim_count(wattbezug, "openWB/set/counter/"+str(counter_num)+"/", counter.data["set"])