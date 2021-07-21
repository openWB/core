#!/usr/bin/python 
import struct 
from pymodbus.client.sync import ModbusTcpClient 

from ...helpermodules import pub
from ...helpermodules import simcount

def read_gavazzi(counter):
    counter_num = counter.counter_num
    client = ModbusTcpClient(counter.data["config"]["config"]["carlogavazzi_lan"]["ip_address"], port=502) 
    sdmid = 1 

    #Voltage
    resp = client.read_input_registers(0x00,2, unit=sdmid)
    all = format(resp.registers[1], '04x') + format(resp.registers[0], '04x')
    voltage1 = float(struct.unpack('>i', all.decode('hex'))[0])
    voltage1 = float("%.1f" % voltage1) / 10
    resp = client.read_input_registers(0x02,2, unit=sdmid)
    all = format(resp.registers[1], '04x') + format(resp.registers[0], '04x')
    voltage2 = float(struct.unpack('>i', all.decode('hex'))[0])
    voltage2 = float("%.1f" % voltage2) / 10
    resp = client.read_input_registers(0x04,2, unit=sdmid)
    all = format(resp.registers[1], '04x') + format(resp.registers[0], '04x')
    voltage3 = float(struct.unpack('>i', all.decode('hex'))[0])
    voltage3 = float("%.1f" % voltage3) / 10
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/voltage", [voltage1, voltage2, voltage3])

    #phasen watt
    resp = client.read_input_registers(0x12,2, unit=sdmid)
    all = format(resp.registers[1], '04x') + format(resp.registers[0], '04x')
    finalw1 = int(struct.unpack('>i', all.decode('hex'))[0] / 10)
    resp = client.read_input_registers(0x14,2, unit=sdmid)
    all = format(resp.registers[1], '04x') + format(resp.registers[0], '04x')
    finalw2 = int(struct.unpack('>i', all.decode('hex'))[0] / 10)
    resp = client.read_input_registers(0x16,2, unit=sdmid)
    all = format(resp.registers[1], '04x') + format(resp.registers[0], '04x')
    finalw3 = int(struct.unpack('>i', all.decode('hex'))[0] / 10)
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_phase", [finalw1, finalw2, finalw3])
    
    finalw= finalw1 + finalw2 + finalw3
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_all", finalw)

    #ampere
    resp = client.read_input_registers(0x0C,2, unit=sdmid)
    all = format(resp.registers[1], '04x') + format(resp.registers[0], '04x')
    lla1 = float(struct.unpack('>i', all.decode('hex'))[0])
    lla1 = float("%.1f" % lla1) / 1000
    resp = client.read_input_registers(0x0E,2, unit=sdmid)
    all = format(resp.registers[1], '04x') + format(resp.registers[0], '04x')
    lla1 = float(struct.unpack('>i', all.decode('hex'))[0])
    lla2 = float("%.1f" % lla1) / 1000
    resp = client.read_input_registers(0x10,2, unit=sdmid)
    all = format(resp.registers[1], '04x') + format(resp.registers[0], '04x')
    lla1 = float(struct.unpack('>i', all.decode('hex'))[0])
    lla3 = float("%.1f" % lla1) / 1000
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/current", [abs(lla1), abs(lla2). abs(lla3)])

    #evuhz
    resp = client.read_input_registers(0x33,2, unit=sdmid)
    hz = resp.registers[0] / 10
    evuhz = float("%.2f" % hz)
    if evuhz > 100:
        evuhz=float(evuhz / 10)
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/frequency", evuhz)

    simcount.sim_count(finalw, "openWB/set/counter/"+str(counter_num)+"/", counter.data["set"])
