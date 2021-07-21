#!/usr/bin/python
import sys
# import os
# import time
# import getopt
# import struct
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.constants import Endian
from pymodbus.payload import BinaryPayloadDecoder

from ...helpermodules import pub

def ReadUInt32(client, addr):
    data = client.read_holding_registers(addr, 2, unit=71)
    UInt32register = BinaryPayloadDecoder.fromRegisters(data.registers, byteorder=Endian.Big, wordorder=Endian.Big)
    result = UInt32register.decode_32bit_uint()
    return(result)


def ReadInt32(client, addr):
    data = client.read_holding_registers(addr, 2, unit=71)
    Int32register = BinaryPayloadDecoder.fromRegisters(data.registers, byteorder=Endian.Big, wordorder=Endian.Big)
    result = Int32register.decode_32bit_int()
    return(result)


def ReadUInt64(client, addr):
    data = client.read_holding_registers(addr, 4, unit=71)
    UInt64register = BinaryPayloadDecoder.fromRegisters(data.registers, byteorder=Endian.Big, wordorder=Endian.Big)
    result = UInt64register.decode_64bit_uint()
    return(result)

def read_kostal_smart_energy_meter(counter):
    counter_num = counter.counter_num
    client = ModbusTcpClient(counter.data["config"]["config"]["janitza"]["ip_address"], port="502")
    client.connect()
        
    voltage1 = ReadUInt32(client, 62) * 0.001
    voltage2 = ReadUInt32(client, 102) * 0.001
    voltage3 = ReadUInt32(client, 142) * 0.001
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/voltage", [voltage1, voltage2, voltage3])

    bezugkwh = ReadUInt64(512) * 0.1
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/imported", bezugkwh)

    bezugw1p = ReadUInt32(client, 40) * 0.1
    bezugw1m = ReadUInt32(client, 42) * 0.1
    bezugw1 = bezugw1p if bezugw1p >= bezugw1m else -bezugw1m
    bezugw2p = ReadUInt32(client, 80) * 0.1
    bezugw2m = ReadUInt32(client, 82) * 0.1
    bezugw2 = bezugw2p if bezugw2p >= bezugw2m else -bezugw2m
    bezugw3p = ReadUInt32(client, 120) * 0.1
    bezugw3m = ReadUInt32(client, 122) * 0.1
    bezugw3 = bezugw3p if bezugw3p >= bezugw3m else -bezugw3m
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_phase", [bezugw1, bezugw2, bezugw3])

    bezuga1 = ReadUInt32(client, 60) * 0.001
    bezuga2 = ReadUInt32(client, 100) * 0.001
    bezuga3 = ReadUInt32(client, 140) * 0.001
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/current", [bezuga1, bezuga2, bezuga3])

    wattbezugp = ReadUInt32(client, 0) * 0.1
    wattbezugm = ReadUInt32(client, 2) * 0.1
    wattbezug = wattbezugp if wattbezugp >= wattbezugm else -wattbezugm
    finalwattbezug = int(wattbezug)
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_all", finalwattbezug)

    einspeisungkwh = ReadUInt64(client, 516) * 0.1
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/exported", einspeisungkwh)

    evuhz = ReadUInt32(client, 26) * 0.001
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/frequency", evuhz)

    evupf1 = ReadInt32(client, 64) * 0.001
    evupf2 = ReadInt32(client, 104) * 0.001
    evupf3 = ReadInt32(client, 144) * 0.001
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_factor", [evupf1, evupf2, evupf3])
