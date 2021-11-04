#!/usr/bin/python3
from pymodbus.client.sync import ModbusTcpClient
import re
import time

from ...helpermodules import log
from ...helpermodules import pub


def read_ip_evse(cp):
    try:
        cp_num = cp.cp_num

        ip_address = cp.data["config"]["connection_module"]["ip_evse"]["ip_address"]
        id = cp.data["config"]["connection_module"]["ip_evse"]["id"]

        client = ModbusTcpClient(ip_address, port=8899)
        rq = client.read_holding_registers(1002, 1, unit=id)
        state = int(rq.registers[0])

        if state == "" or re.search("^[0-9]+$", state) is None:
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
    except Exception as e:
        log.exception_logging(e)


def write_ip_evse(ip_address, id, current):
    try:
        client = ModbusTcpClient(ip_address, port=8899)
        rq = client.write_registers(1000, current, unit=id)
    except Exception as e:
        log.exception_logging(e)

def perform_phase_switcht(ip_address, id, duration, phases_to_use):
    client = ModbusTcpClient(ip_address, port=8899)
    if ( phases_to_use == 1 ):
        rq = client.write_register(0x0001, 256, unit=id)
        time.sleep(duration)
        rq = client.write_register(0x0001, 512, unit=id)

    elif ( phases_to_use == 3 ):
        rq = client.write_register(0x0002, 256, unit=id)
        time.sleep(duration)
        rq = client.write_register(0x0002, 512, unit=id)

def perform_cp_interruption(ip_address, id, duration):
    client = ModbusTcpClient(ip_address, port=8899)
    rq = client.write_register(0x0001, 256, unit=id)
    time.sleep(duration)
    rq = client.write_register(0x0001, 512, unit=id)