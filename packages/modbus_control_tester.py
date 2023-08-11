#!/usr/bin/env python3
from enum import Enum
from pymodbus.client.sync import ModbusTcpClient
import time
from modules.common import modbus


class Actions(Enum):
    READ_NUMBER_INPUT_REG = 0
    READ_NUMBER_HOLDING_REG = 1
    READ_STR = 2
    WRITE_VALUE = 3


host = "localhost"
port = 1502
slave_id = 1
start = 300
length = 2
data_type = modbus.ModbusDataType.INT_32
action = Actions.READ_NUMBER_INPUT_REG
try:
    print(time.strftime("%Y-%m-%d %H:%M:%S modbus-tester"))
    print("Parameter:")
    print(f"Host: {host}:{port} auf ModbusID {slave_id}")
    print(f"Startadresse: {start}, Anzahl: {length}, Datentyp: {data_type}")
    print(f"Funktion: {action}")
    if action == Actions.READ_NUMBER_INPUT_REG or action == Actions.READ_NUMBER_HOLDING_REG:
        client = modbus.ModbusTcpClient_(host, port=port)
        if action == Actions.READ_NUMBER_INPUT_REG:
            if length > 1:
                resp = client.read_input_registers(start, [data_type]*length, unit=slave_id)
            else:
                resp = client.read_input_registers(start, data_type, unit=slave_id)
        elif action == Actions.READ_NUMBER_HOLDING_REG:
            if length > 1:
                resp = client.read_holding_registers(start, [data_type]*length, unit=slave_id)
            else:
                resp = client.read_holding_registers(start, data_type, unit=slave_id)
        print("Ergebnis: " + str(resp))
    elif action == Actions.READ_STR:
        client = modbus.ModbusTcpClient_(host, port=port)
        if action == Actions.READ_NUMBER_INPUT_REG:
            resp = client.read_input_registers(start, [modbus.ModbusDataType.INT_16]*length, unit=slave_id)
        elif action == Actions.READ_NUMBER_HOLDING_REG:
            resp = client.read_holding_registers(start, [modbus.ModbusDataType.INT_16]*length, unit=slave_id)
        string = b"".join(resp)
        print("Ergebnis: " + str(string))
    elif action == Actions.WRITE_VALUE:
        client = ModbusTcpClient(host, port=port)
        rq = client.write_registers(20100, 14, unit=slave_id)
except Exception as e:
    print("Exception "+str(e))
