#!/usr/bin/python3
from pymodbus.transaction import ModbusRtuFramer
from pymodbus.client.sync import ModbusTcpClient

from ...helpermodules import log

def write_master_eth_framer(current):
    try:
        client = ModbusTcpClient('192.168.193.18', port=8899, framer=ModbusRtuFramer)
        rq = client.write_registers(1000, current, unit=1)
    except Exception as e:
        log.exception_logging(e)
