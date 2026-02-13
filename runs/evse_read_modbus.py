#!/usr/bin/env python3
import sys

sys.path.append("/var/www/html/openWB/packages")
try:
    from modules.chargepoints.internal_openwb.config import InternalChargepointMode
    from modules.internal_chargepoint_handler.clients import get_modbus_client
    from modules.common.modbus import ModbusDataType
except Exception as e:
    # Durch try-except werden die Imports vom Formatierer nicht an den Dateianfang geschoben.
    print(e)

mode = sys.argv[1]
local_charge_point_num = int(sys.argv[2])
register = int(sys.argv[3])
num = int(sys.argv[4])

client, evse_ids = get_modbus_client(InternalChargepointMode(mode), local_charge_point_num)
print(client.read_holding_registers(register, [ModbusDataType.INT_16]*num, unit=evse_ids[0]))
