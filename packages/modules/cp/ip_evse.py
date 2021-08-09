#!/usr/bin/python3
from pymodbus.client.sync import ModbusTcpClient
import re

from ...helpermodules import log
from ...helpermodules import pub


def read_ip_evse(cp):
    cp_num = cp.cp_num

    ip_address = cp.data["config"]["connection_module"]["ip_evse"]["ip_address"]
    id = cp.data["config"]["connection_module"]["ip_evse"]["id"]

    client = ModbusTcpClient(ip_address, port=8899)
    rq = client.read_holding_registers(1002, 1, unit=id)
    state = int(rq.registers[0])

    if state == "" or re.search("^[0-9]+$", state) == None:
        # vorherigen Steckerstatus beibehalten (nichts publishen)
        log.message_debug_log("error", "Modbus EVSE read CP"+str(cp_num)+" issue - using previous state")
    if state > 1:
        plug_state = True
    else:
        plug_state = False
    pub.pub("openWB/set/chargepoint/"+str(cp_num)+"/get/plug_state", plug_state)
    if plug_state > 2:
        charge_state = True
    else:
        charge_state = False
    pub.pub("openWB/set/chargepoint/"+str(cp_num)+"/get/charge_state", charge_state)
