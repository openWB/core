#!/usr/bin/python3
import os
import re
import stat
import subprocess
import time
from pymodbus.client.sync import ModbusSerialClient

from ...helpermodules import log
from ...helpermodules import pub


def read_modbus_evse(cp):
    try:
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

        state = _read_regs(source, id, 1002, 1)

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
    except Exception as e:
        log.exception_logging(e)

def _read_regs(source, id, reg, num):
    try:
        client = ModbusSerialClient(method = "rtu", port=source, baudrate=9600, stopbits=1, bytesize=8, timeout=1)
        rq = client.read_holding_registers(reg,num,unit=id)
        return int(rq.registers[0])
    except Exception as e:
        log.exception_logging(e)

def _write_regs(source, id, reg, value):
    try:
        client = ModbusSerialClient(method = "rtu", port=source, baudrate=9600, stopbits=1, bytesize=8, timeout=1)
        rq = client.write_registers(reg, value, unit=id)
    except Exception as e:
        log.exception_logging(e)

def write_modbus_evse(cp):
    try:
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
                pub.pub("openWB/set/chargepoint/"+str(cp.cp_num)+"/config", {"connection_module": {"config": {"modbus_evse": {"source": source}}}})
                id = 1
        
        _write_regs(source, id, 1000, cp.data["set"]["current"])
    except Exception as e:
        log.exception_logging(e)

def check_modbus_evse(cp):
    try:
        source = cp.data["config"]["connection_module"]["modbus_evse"]["source"]
        ip_address = cp.data["config"]["connection_module"]["modbus_evse"]["ip_address"]
        if "virtual" in source:
            try:
                subprocess.check_output(['ps ax |grep -v grep |grep "socat", "pty,link="+str(source)+",raw", "tcp:"+str(ip_address)+":26" > /dev/null'])
            except:
                subprocess.Popen(["sudo", "socat", "pty,link="+str(source)+",raw", "tcp:"+str(ip_address)+":26"])
        evsedinstat= _read_regs(source, id, 1000, 1)
        time.sleep(1)
        if evsedinstat == cp.data["set"]["current"]:
            log.message_debug_log("debug", "LP"+str(cp.cp_num)+" Modbus-Stromstaerke ist korrekt.")
        else:
            log.message_debug_log("error", "LP"+str(cp.cp_num)+" Modbus-Stromstaerke "+str(evsedinstat)+" ist nicht korrekt.")
            _write_regs(source, id, 1000, cp.data["set"]["current"])
    except Exception as e:
        log.exception_logging(e)