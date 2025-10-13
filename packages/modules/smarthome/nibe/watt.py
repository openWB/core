#!/usr/bin/python3
import logging
import sys
import json
from pymodbus.client.sync import ModbusTcpClient

log = logging.getLogger(__name__)

# get variables from arguments
devicenumber = str(sys.argv[1])  # SmartHome device number
SERVER_HOST = str(sys.argv[2])  # IP of server to connect to

SERVER_PORT = "502"  # TCP port to connect to, should be moved into argument as well

# Registers:
# https://www.waermepumpen-24.de/fileadmin/kaelteklima/Dokumente/W%C3%A4rmepumpen/modbus-ih-s-serie-v-2335.pdf
# 2166 power
# 2740 configure SG Ready input A or B via Modbus
# 2741 activate/deactive Modbus Aux function - can be enabled directly on Heatpump menu 7.4

CurrentPowerRegisterAddress = 2166  # register for current power reading

# need to specify framer to enable RTUoverTCP
client = ModbusTcpClient(SERVER_HOST, SERVER_PORT)

# Aktueller Verbrauch
resp = client.read_input_registers(CurrentPowerRegisterAddress, 1, unit=1)

if resp and hasattr(resp, "registers"):
    CurrentPower = resp.registers[0]  # Get the first register value
else:
    CurrentPower = None  # Handle error case

answer = '{"power":' + str(CurrentPower) + '}'
with open('/var/www/html/openWB/ramdisk/smarthome_device_ret' + str(devicenumber), 'w') as f1:
    json.dump(answer, f1)

client.close()  # clean disconnect from modbus server
