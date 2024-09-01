#!/usr/bin/python3
import sys
sys.path.append("/var/www/html/openWB/packages")
try:
    from modules.internal_chargepoint_handler.clients import get_modbus_client
except Exception as e:
    # Durch try-except werden die Imports vom Formatierer nicht an den Dateianfang geschoben.
    print(e)

local_chargepoint_num = int(sys.argv[1])
register = int(sys.argv[2])
value = int(sys.argv[3])

client, evse_ids = get_modbus_client(local_chargepoint_num)
client.write_registers(register, value, unit=evse_ids[local_chargepoint_num])
