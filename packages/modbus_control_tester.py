#!/usr/bin/env python3
from collections import namedtuple
from enum import Enum
import logging
import struct
from typing import Optional
from pymodbus.client.sync import ModbusTcpClient
import time
from modules.common import modbus
from modules.common.modbus import ModbusDataType
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
read_client = modbus.ModbusTcpClient_(host, port=port)
Register = namedtuple("Register", "reg, action, length, type, name, expected")
REGISTERS = (
    Register(10100, Actions.READ_NUMBER, 1, ModbusDataType.INT_32, name="Actual Power", expected=(0, 0)),
    Register(10102, Actions.READ_NUMBER, 1, ModbusDataType.INT_32,
             name="Wh Imported Counter", expected=(0, float("inf"))),
    Register(10104, Actions.READ_NUMBER, 1, ModbusDataType.INT_16, name="Phase 1 Voltage", expected=(22000, 24000)),
    Register(10105, Actions.READ_NUMBER, 1, ModbusDataType.INT_16, name="Phase 2 Voltage", expected=(22000, 24000)),
    Register(10106, Actions.READ_NUMBER, 1, ModbusDataType.INT_16, name="Phase 3 Voltage", expected=(22000, 24000)),
    Register(10108, Actions.READ_NUMBER, 1, ModbusDataType.INT_16, name="Phase 1 Ampere", expected=(0, 0)),
    Register(10109, Actions.READ_NUMBER, 1, ModbusDataType.INT_16, name="Phase 2 Ampere", expected=(0, 0)),
    Register(10110, Actions.READ_NUMBER, 1, ModbusDataType.INT_16, name="Phase 3 Ampere", expected=(0, 0)),
    Register(10114, Actions.READ_NUMBER, 1, ModbusDataType.INT_16, name="Plugged Status", expected=(1, 1)),
    Register(10115, Actions.READ_NUMBER, 1, ModbusDataType.INT_16, name="Charging Active", expected=(0, 0)),
    Register(10116, Actions.READ_NUMBER, 1, ModbusDataType.INT_16, name="Actual A Configured", expected=(0, 0)),
    Register(10130, Actions.READ_NUMBER, 1, ModbusDataType.INT_16, name="Phase 1 Watt", expected=(0, 0)),
    Register(10131, Actions.READ_NUMBER, 1, ModbusDataType.INT_16, name="Phase 2 Watt", expected=(0, 0)),
    Register(10132, Actions.READ_NUMBER, 1, ModbusDataType.INT_16, name="Phase 3 Watt", expected=(0, 0)),
    Register(10141, Actions.READ_NUMBER, 1, ModbusDataType.INT_32, name="Wh Exported Counter", expected=(0, 0)),
    Register(10143, Actions.READ_NUMBER, 1, ModbusDataType.INT_16, name="Type of Hardware", expected=(1, 1)),
    Register(10150, Actions.READ_STR, 10, ModbusDataType.INT_16,
             name="Serial Number of Chargepoint", expected="noSerialNumber"),
    Register(10160, Actions.READ_STR, 10, ModbusDataType.INT_16, name="ID-Tag", expected='0004141661'),
)


def heartbeat_read():
    read_client.read_input_registers(10104, modbus.ModbusDataType.INT_16, unit=slave_id)


def read_reg(register: int,
             action: Actions,
             length: int,
             data_type: Optional[ModbusDataType] = None,
             write_value: Optional[int] = None):
    try:
        if action == Actions.READ_NUMBER:
            if read_mode == ReadMode.READ_INPUT_REG:
                if length > 1:
                    resp = read_client.read_input_registers(register, [data_type]*length, unit=slave_id)
                else:
                    resp = read_client.read_input_registers(register, data_type, unit=slave_id)
            elif read_mode == ReadMode.READ_HOLDING_REG:
                if length > 1:
                    resp = read_client.read_holding_registers(register, [data_type]*length, unit=slave_id)
                else:
                    resp = read_client.read_holding_registers(register, data_type, unit=slave_id)
            return resp
        elif action == Actions.READ_STR:
            if read_mode == ReadMode.READ_INPUT_REG:
                resp = read_client.read_input_registers(register, [modbus.ModbusDataType.INT_16]*length, unit=slave_id)
            elif read_mode == ReadMode.READ_HOLDING_REG:
                resp = read_client.read_holding_registers(
                    register, [modbus.ModbusDataType.INT_16]*length, unit=slave_id)
            string = ""
            for word in resp:
                string += struct.pack(">h", word).decode("utf-8")
            return resp
        elif action == Actions.WRITE_VALUE:
            client = ModbusTcpClient(host, port=port)
            client.write_registers(register, write_value, unit=slave_id)
            return None
    except Exception:
        log.exception("Fehler")


def access_single_register():
    # Modify
    register = 10102
    action = Actions.READ_NUMBER
    length = 1  # 1 in action READ_NUMBER and WRITE_VALUE, Length of str in action READ_STR
    data_type = ModbusDataType.INT_32  # used only in action READ_NUMBER
    write_value = 750  # used only in action WRITE_VALUE
    print(f"Startadresse: {register}, Anzahl: {length}, Datentyp: {data_type}")
    print(f"Funktion: {action}")
    heartbeat_read()
    resp = read_reg(register, action, length, data_type, write_value)
    if action == Actions.READ_NUMBER or action == Actions.READ_STR:
        print(f"Ergebnis: {resp}")


def evaluate_reg(reg):
    resp = read_reg(reg.reg, reg.action, reg.length, reg.type)
    print(f"Register: {reg.reg}, Name: {reg.name}, Ergebnis: {resp}")
    if reg.action == Actions.READ_NUMBER:
        if resp >= reg.expected[0] and resp <= reg.expected[1]:
            return resp
        else:
            raise Exception(
                f"Register: {reg.reg}, Name: {reg.name} mit Ergebnis: "
                f"{resp} ist ungleich dem erwarteten Ergebnis {reg.expected}")
    elif reg.action == Actions.READ_STR:
        string = ""
        if resp:
            for word in resp:
                if word != 0:
                    string += struct.pack(">h", word).decode("utf-8")
        if string == reg.expected:
            return string
        else:
            raise Exception(
                f"Register: {reg.reg}, Name: {reg.name} mit Ergebnis: "
                f"{string} ist nicht Teil des erwarteten Ergebnis {reg.expected}")


def read_all_registers():
    heartbeat_read()
    for reg in REGISTERS:
        if reg.reg == 10160:
            while True:
                try:
                    if evaluate_reg(reg):
                        break
                except Exception:
                    print("Bitte ID-Tag erfassen")
                    time.sleep(1)
        else:
            evaluate_reg(reg)
    else:
        print("Test abgeschlossen, alle Register haben das erwartete Ergebnis geliefert.")


print(time.strftime("%Y-%m-%d %H:%M:%S modbus-tester"))
print(f"Host: {host}:{port} auf ModbusID {slave_id}")
read_all_registers()
# access_single_register()
