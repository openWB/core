#!/usr/bin/python3
import sys
import json
from pymodbus.transaction import ModbusRtuFramer
from pymodbus.client import ModbusTcpClient

# get variables from arguments
devicenumber = str(sys.argv[1])  # SmartHome device number
SERVER_HOST = str(sys.argv[2])  # IP of server to connect to
MODBUS_DEVICEID = int(sys.argv[3])  # Modbus device ID

SERVER_PORT = "502"  # TCP port to connect to, should be moved into argument as well

# Registers:
# https://github.com/gituser-rk/orno-modbus-mqtt/blob/master/Register%20description%20OR-WE-514%26OR-WE-515.pdf
# 0x131 frequency
# 0x131 voltage
# 0x141 power
# 0xA001 (total energy rate1)

TotalEnergyRegisterAddress = 0xA001  # register for total energy
CurrentPowerRegisterAddress = 0x141  # register for current power reading


# need to specify framer to enable RTUoverTCP
client = ModbusTcpClient(SERVER_HOST, SERVER_PORT, framer=ModbusRtuFramer)

# KWH Total Import
resp = client.read_holding_registers(TotalEnergyRegisterAddress, 1, device_id=MODBUS_DEVICEID)
TotalEnergy = int(resp.registers[0]) * 10  # Value is in 0.01kWh, need to convert to Wh

# Aktueller Verbrauch
resp = client.read_holding_registers(CurrentPowerRegisterAddress, 1, device_id=MODBUS_DEVICEID)
CurrentPower = int(resp.registers[0])

answer = {"power": CurrentPower, "powerc": TotalEnergy}
with open(f'/var/www/html/openWB/ramdisk/smarthome_device_ret{devicenumber}', 'w') as f1:
    json.dump(answer, f1)

client.close()  # clean disconnect from modbus server
