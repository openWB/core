#!/usr/bin/env python3
import time
from typing import Callable

import pymodbus
from pymodbus.constants import Endian

import sys
sys.path.append("/var/www/html/openWB/packages")

try:
    from modules.common import modbus
except Exception as e:
    print(e)


def try_read(function: Callable, **kwargs) -> str:
    result = "--"
    try:
        result = str(function(**kwargs))
    except pymodbus.exceptions.ConnectionException:
        # Can happen on concurrent access, retry once
        result = str(function(**kwargs))
    finally:
        return result


host = sys.argv[1]
port = int(sys.argv[2])
slave_id = int(sys.argv[3])
start = int(sys.argv[4])
end = int(sys.argv[5])
func = int(sys.argv[6])

print(time.strftime("%Y-%m-%d %H:%M:%S modbus-finder"))
print("Parameter:")
print("Host: " + host)
print("Port: " + str(port))
print("Modbus ID: " + str(slave_id))
print("Startadresse: " + str(start))
print("Endadresse: " + str(end))
print("Funktion: " + str(func) + "\n")
try:
    client = modbus.ModbusTcpClient_(host, port=port)
    function: Callable
    if func == 4:
        function = client.read_input_registers
    elif func == 3:
        function = client.read_holding_registers
    else:
        print("unsupported function code: " + str(func))
        exit(1)

    print("Address;INT_16;UINT_16;INT_32;UINT_32")
    for address in range(start, end):
        resp_INT_16 = try_read(function, address=address, types=modbus.ModbusDataType.INT_16, unit=slave_id)
        resp_UINT_16 = try_read(function, address=address, types=modbus.ModbusDataType.UINT_16, unit=slave_id)
        resp_INT_32 = try_read(function, address=address, types=modbus.ModbusDataType.INT_32, wordorder=Endian.Little,
                               unit=slave_id)
        resp_UINT_32 = try_read(function, address=address, types=modbus.ModbusDataType.UINT_32, wordorder=Endian.Little,
                                unit=slave_id)
        print(f"{address};{resp_INT_16};{resp_UINT_16};{resp_INT_32};{resp_UINT_32}")
except Exception as e:
    print("Exception " + str(e))
