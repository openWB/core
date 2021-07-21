import struct
from pymodbus.client.sync import ModbusTcpClient

from ...helpermodules import pub

def read_sma_sunny_island(bat):
    bat_num = bat.bat_num
    ipaddress = bat.data["config"]["config"]["sma_sunny_island"]["ip_address"]

    client = ModbusTcpClient(ipaddress, port=502)

    # print "SoC batt"
    resp= client.read_holding_registers(30845,2,unit=3)
    value1 = resp.registers[0]
    value2 = resp.registers[1]
    all = format(value1, '04x') + format(value2, '04x')
    final = int(struct.unpack('>i', all.decode('hex'))[0])
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/soc", final)

    # print "be-entladen watt"
    resp= client.read_holding_registers(30775,2,unit=3)
    value1 = resp.registers[0]
    value2 = resp.registers[1]
    all = format(value1, '04x') + format(value2, '04x')
    ladung = int(struct.unpack('>i', all.decode('hex'))[0]) * -1
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/power", final)

    # print "import wh"
    resp= client.read_holding_registers(30595,2,unit=3)
    value1 = resp.registers[0]
    value2 = resp.registers[1]
    all = format(value1, '04x') + format(value2, '04x')
    ladung = int(struct.unpack('>i', all.decode('hex'))[0])
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/imported", ladung)

    # print "exportwh"
    resp= client.read_holding_registers(30597,2,unit=3)
    value1 = resp.registers[0]
    value2 = resp.registers[1]
    all = format(value1, '04x') + format(value2, '04x')
    ladung = int(struct.unpack('>i', all.decode('hex'))[0])
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/exported", ladung)
