#!/usr/bin/python
import sys
import struct
from pymodbus.client.sync import ModbusTcpClient

from ...helpermodules import pub
from ...helpermodules import simcount

def read_powerdog(counter):
    counter_num = counter.counter_num
    client = ModbusTcpClient(counter.data["config"]["config"]["powerdog"]["ip_address"], port=502)

    #new
    resp = client.read_input_registers(40002,2, unit=1)
    all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
    pvwatt = int(struct.unpack('>i', all.decode('hex'))[0])
    resp = client.read_input_registers(40026,2, unit=1)
    all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
    hausverbrauch = int(struct.unpack('>i', all.decode('hex'))[0])
    final=hausverbrauch-pvwatt

    #evu punkt
    #resp = client.read_input_registers(40000,2, unit=1)
    #all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
    #finaleinspeisung = int(struct.unpack('>i', all.decode('hex'))[0])
    #gridw= finaleinspeisung

    #resp = client.read_input_registers(40024,2, unit=1)
    #all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
    #finaleinspeisung = int(struct.unpack('>i', all.decode('hex'))[0])
    #hausw= finaleinspeisung

    #if gridw > 10:
    #    final=gridw *-1
    #else:
    #    final=hausw
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_all", final)
    simcount.sim_count(final, "openWB/set/counter/"+str(counter_num)+"/", counter.data["set"])