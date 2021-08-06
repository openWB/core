import struct
from pymodbus.client.sync import ModbusTcpClient

from ...helpermodules import pub

def read_mpmp3pm(bat):
    bat_num = bat.bat_num
    client = ModbusTcpClient('192.168.193.19', port=8899)

    resp = client.read_input_registers(0x0002,4, unit=1)
    value1 = resp.registers[0] 
    value2 = resp.registers[1] 
    all = format(value1, '04x') + format(value2, '04x')
    ikwh = int(struct.unpack('>i', all.decode('hex'))[0]) 
    ikwh = float(ikwh) * 10
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/imported", ikwh)

    # total watt
    resp = client.read_input_registers(0x26,2, unit=1)
    value1 = resp.registers[0] 
    value2 = resp.registers[1] 
    all = format(value1, '04x') + format(value2, '04x')
    final = int(struct.unpack('>i', all.decode('hex'))[0]) / 100
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/power", final)

    # export kwh
    resp = client.read_input_registers(0x0004,4, unit=1)
    value1 = resp.registers[0] 
    value2 = resp.registers[1] 
    all = format(value1, '04x') + format(value2, '04x')
    ekwh = int(struct.unpack('>i', all.decode('hex'))[0]) 
    ekwh = float(ekwh) * 10
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/exported", ekwh)