#!/usr/bin/python3
import sys

from modules.internal_chargepoint_handler.clients import get_modbus_client

local_chargepoint_num = int(sys.argv[1])
register = int(sys.argv[3])
value = int(sys.argv[4])

client, evse_ids = get_modbus_client(local_chargepoint_num)
rq = client.delegate.write_registers(register, value, unit=evse_ids[local_chargepoint_num])
