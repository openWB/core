#!/usr/bin/python3
import sys
import struct
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian
from pymodbus.client.sync import ModbusTcpClient

from ...helpermodules import pub


def read_janitza(counter):
    counter_num = counter.counter_num
    client = ModbusTcpClient(counter.data["config"]["config"]["janitza"]["ip_address"], port=502)

    #rq = client.read_holding_registers(0,8,unit=5)
    #print(rq.registers)
    modbusid = 1
    readreg = 19026
    reganzahl = 2

    rq = client.read_holding_registers(readreg,reganzahl,unit=modbusid)
    #print(rq.registers[0])
    #print(rq.registers[1])
    #print(rq.registers[2])
    #print(rq.registers[3])

    #value1 = rq.registers[0] 
    #value2 = rq.registers[1] 
    #all = format(value1, '04x') + format(value2, '04x')
    #final = int(struct.unpack('>i', all.decode('hex'))[0])
    #print(str(final))

    FRegister_232 = BinaryPayloadDecoder.fromRegisters(rq.registers, byteorder=Endian.Big, wordorder=Endian.Little)
    Current_phase_2_powermeter = round(FRegister_232.decode_32bit_float(),2)

    voltage = struct.unpack('>f',struct.pack('>HH',*rq.registers))[0]
    voltage2 = int(voltage)
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_all", voltage)
