#!/usr/bin/env python3
from enum import Enum
import logging
import struct
from pymodbus.client.sync import ModbusTcpClient
import time
from modules.common import modbus

log = logging.getLogger()

class Actions(Enum):
    READ_NUMBER = 0
    READ_STR = 1
    WRITE_VALUE = 2


class ReadMode(Enum):
    READ_INPUT_REG = 0
    READ_HOLDING_REG = 1

# Don't modify
host = "localhost"
port = 1502
slave_id = 1
read_mode = ReadMode.READ_INPUT_REG

# Test
start = 10171
length = 1
data_type = modbus.ModbusDataType.INT_16
action = Actions.WRITE_VALUE
write_value = 750


# Heartbeat-Read
read_client = modbus.ModbusTcpClient_(host, port=port)
read_client.read_input_registers(10104, modbus.ModbusDataType.INT_16, unit=slave_id)
try:
    print(time.strftime("%Y-%m-%d %H:%M:%S modbus-tester"))
    print("Parameter:")
    print(f"Host: {host}:{port} auf ModbusID {slave_id}")
    print(f"Startadresse: {start}, Anzahl: {length}, Datentyp: {data_type}")
    print(f"Funktion: {action}")
    if action == Actions.READ_NUMBER:
        if read_mode == ReadMode.READ_INPUT_REG:
            if length > 1:
                resp = read_client.read_input_registers(start, [data_type]*length, unit=slave_id)
            else:
                resp = read_client.read_input_registers(start, data_type, unit=slave_id)
        elif read_mode == ReadMode.READ_HOLDING_REG:
            if length > 1:
                resp = read_client.read_holding_registers(start, [data_type]*length, unit=slave_id)
            else:
                resp = read_client.read_holding_registers(start, data_type, unit=slave_id)
        print("Ergebnis: " + str(resp))
    elif action == Actions.READ_STR:
        if read_mode == ReadMode.READ_INPUT_REG:
            resp = read_client.read_input_registers(start, [modbus.ModbusDataType.INT_16]*length, unit=slave_id)
        elif read_mode == ReadMode.READ_HOLDING_REG:
            resp = read_client.read_holding_registers(start, [modbus.ModbusDataType.INT_16]*length, unit=slave_id)
        string = ""
        for word in resp:
            string += struct.pack(">h", word).decode("utf-8")
        print("Ergebnis: " + str(string))
    elif action == Actions.WRITE_VALUE:
        client = ModbusTcpClient(host, port=port)
        rq = client.write_registers(start, write_value, unit=slave_id)
except Exception as e:
    log.exception("Fehler")
