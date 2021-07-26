import struct
from pymodbus.transaction import ModbusRtuFramer
from pymodbus.client.sync import ModbusTcpClient

from ...helpermodules import pub

def read_ethmpm3pm(cp):
    cp_num = cp.cp_num
    if cp.data["config"]["power_module"]["selected"] == "ethmpm3pm":
        client = ModbusTcpClient('192.168.193.16', port=8899)
    elif cp.data["config"]["power_module"]["selected"] == "ethmpm3pm_framer":
        client = ModbusTcpClient('192.168.193.18', port=8899, framer=ModbusRtuFramer)
    elif cp.data["config"]["power_module"]["selected"] == "ethmpm3pm_third_cp":
        client = ModbusTcpClient('192.168.193.26', port=8899)
    resp = client.read_input_registers(0x0002,4, unit=5)
    value1 = resp.registers[0] 
    value2 = resp.registers[1] 
    all = format(value1, '04x') + format(value2, '04x')
    ikwh = int(struct.unpack('>i', all.decode('hex'))[0]) 
    ikwh = float(ikwh) /100
    pub.pub("openWB/set/chargepoint/"+str(cp_num)+"/get/counter", ikwh)


    resp = client.read_input_registers(0x0E,2, unit=5)
    lla1 = resp.registers[1]
    lla1 = float(lla1) / 100
    resp = client.read_input_registers(0x10,2, unit=5)
    lla2 = resp.registers[1]
    lla2 = float(lla2) / 100
    resp = client.read_input_registers(0x12,2, unit=5)
    lla3 = resp.registers[1]
    lla3 = float(lla3) / 100
    pub.pub("openWB/set/chargepoint/"+str(cp_num)+"/get/current", [lla1, lla2, lla3])

    resp = client.read_input_registers(0x26,2, unit=5)
    value1 = resp.registers[0] 
    value2 = resp.registers[1] 
    all = format(value1, '04x') + format(value2, '04x')
    final = int(struct.unpack('>i', all.decode('hex'))[0]) / 100
    if final < 10:
        final = 0
    resp = client.read_input_registers(0x08,4, unit=5)
    voltage1 = resp.registers[1]
    voltage1 = float(voltage1) / 10
    resp = client.read_input_registers(0x0A,4, unit=5)
    voltage2 = resp.registers[1]
    voltage2 = float(voltage2) / 10
    resp = client.read_input_registers(0x0C,4, unit=5)
    voltage3 = resp.registers[1]
    voltage3 = float(voltage3) / 10
    pub.pub("openWB/set/chargepoint/"+str(cp_num)+"/get/voltage", [voltage1, voltage2, voltage3])

