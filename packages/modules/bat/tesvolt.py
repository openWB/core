import struct
from pymodbus.client.sync import ModbusTcpClient

from ...helpermodules import pub
from ...helpermodules import simcount

def read_tesvolt(bat):
    bat_num = bat.bat_num
    ipaddress = bat.data["config"]["config"]["tesvolt"]["ip_address"]

    client = ModbusTcpClient(ipaddress, port=502)

    # print "SoC batt"
    resp= client.read_input_registers(1056,2,unit=25)
    value1 = resp.registers[0]
    value2 = resp.registers[1]
    all = format(value1, '04x') + format(value2, '04x')
    final = int(struct.unpack('>i', all.decode('hex'))[0])/10
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/soc", final)

    # print "be-entladen watt"
    resp= client.read_input_registers(1012,2,unit=25)
    value1 = resp.registers[0]
    value2 = resp.registers[1]
    all = format(value1, '04x') + format(value2, '04x')
    ladung = int(struct.unpack('>i', all.decode('hex'))[0]) * -1
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/power", ladung)

    simcount.sim_count(ladung, "openWB/set/bat/"+str(bat_num)+"/", bat.data["set"])
