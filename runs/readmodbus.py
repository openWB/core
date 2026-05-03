#!/usr/bin/env python3
import sys
from pymodbus.client import ModbusSerialClient

seradd = str(sys.argv[1])
modbusid = int(sys.argv[2])
readreg = int(sys.argv[3])
reganzahl = int(sys.argv[4])

client = ModbusSerialClient(seradd, baudrate=9600, stopbits=1, bytesize=8, timeout=1)
request = client.read_holding_registers(readreg, count=reganzahl, device_id=modbusid)
if request.isError():
    print('Modbus Error:', request)
else:
    print(request.registers[0])
