#!/usr/bin/python3
from pathlib import Path
import sys


sys.path.append("/var/www/html/openWB/packages")
try:
    from modules.common.modbus import ModbusSerialClient_
except Exception as e:
    # Durch try-except werden die Imports vom Formatierer nicht an den Dateianfang geschoben.
    print(e)

unit = int(sys.argv[3])
register = int(sys.argv[4])
value = int(sys.argv[5])

client = ModbusSerialClient_(str(list(Path("/dev/serial/by-path").glob("*"))[0].resolve()))
client.write_register(register, value, unit=unit)
