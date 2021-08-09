#!/usr/bin/python3
import os
import re
import stat
from pymodbus.client.sync import ModbusSerialClient

from ...helpermodules import log
from ...helpermodules import pub


def read_modbus_evse(cp):
    cp_num = cp.cp_num
    if cp_num == 1:
        if cp.data["config"]["connection_module"]["modbus_evse"]["id"] == 0:
            if "source" in cp.data["config"]["connection_module"]["modbus_evse"]:
                source = cp.data["config"]["connection_module"]["modbus_evse"]["source"]
                id = 1
            else:
                if stat.S_ISBLK(os.stat("/dev/ttyUSB0").st_mode) == True:
                    source = "/dev/ttyUSB0"
                else:
                    source = "/dev/serial0"
                cp.data["config"]["connection_module"]["modbus_evse"]["source"] = source
                pub.pub("openWB/set/chargepoint/"+str(cp_num)+"/config", {"connection_module": {"config": {"modbus_evse": {"source": source}}}})
                id = 1
    else:
        source = cp.data["config"]["connection_module"]["modbus_evse"]["source"]
        id = cp.data["config"]["connection_module"]["modbus_evse"]["id"]

    client = ModbusSerialClient(method="rtu", port=source, baudrate=9600, stopbits=1, bytesize=8, timeout=1)
    rq = client.read_holding_registers(1002, 1, unit=id)
    state = int(rq.registers[0])

    if state == "" or re.search("^[0-9]+$", state) == None:
        # vorherigen Steckerstatus beibehalten (nichts publishen)
        log.message_debug_log("error", "Modbus EVSE read CP"+str(cp_num)+" issue - using previous state")
    if 0 <= state <= 10:
    # LP 2 if 0 <= state <= 7:
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
