#!/usr/bin/python

import struct
from pymodbus.client.sync import ModbusTcpClient

from ...helpermodules import pub
from ...helpermodules import simcount

def read_sbs25(counter):
    counter_num = counter.counter_num
    client = ModbusTcpClient(counter.data["config"]["config"]["sbs25"]["ip_address"], port=502)

    # print "evu watt bezug"
    resp= client.read_holding_registers(30865,2,unit=3)
    value1 = resp.registers[0]
    value2 = resp.registers[1]
    all = format(value1, '04x') + format(value2, '04x')
    bezug = int(struct.unpack('>i', all.decode('hex'))[0])
    resp= client.read_holding_registers(30867,2,unit=3)
    value1 = resp.registers[0]
    value2 = resp.registers[1]
    all = format(value1, '04x') + format(value2, '04x')
    einsp = int(struct.unpack('>i', all.decode('hex'))[0])
    if bezug > 5:
        final=bezug
    else:
        final=einsp * -1
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_all", final)

    simcount.sim_count(final, "openWB/set/counter/"+str(counter_num)+"/", counter.data["set"])
