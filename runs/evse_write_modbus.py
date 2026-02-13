#!/usr/bin/python3
import sys

sys.path.append("/var/www/html/openWB/packages")
try:
    from modules.chargepoints.internal_openwb.config import InternalChargepointMode
    from modules.internal_chargepoint_handler.clients import get_modbus_client
except Exception as e:
    # Durch try-except werden die Imports vom Formatierer nicht an den Dateianfang geschoben.
    print(e)

mode = sys.argv[1]
local_chargepoint_num = int(sys.argv[2])
register = int(sys.argv[3])
value = int(sys.argv[4])

client, evse_ids = get_modbus_client(InternalChargepointMode(mode), local_chargepoint_num)
client.write_register(register, value, unit=evse_ids[0])
