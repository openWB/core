import struct
from pymodbus.client.sync import ModbusTcpClient

from ...helpermodules import pub
from ...helpermodules import simcount

def read_sbs25(bat):
    bat_num = bat.bat_num
    ipaddress = bat.data["config"]["config"]["sbs25"]["ip_address"]

    client = ModbusTcpClient(ipaddress, port=502)

    # print "SoC batt"
    resp= client.read_holding_registers(30845,2,unit=3)
    value1 = resp.registers[0]
    value2 = resp.registers[1]
    all = format(value1, '04x') + format(value2, '04x')
    final = int(struct.unpack('>i', all.decode('hex'))[0])
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/soc", final)

    # print "be-entladen watt"
    resp= client.read_holding_registers(31393,2,unit=3)
    value1 = resp.registers[0]
    value2 = resp.registers[1]
    all = format(value1, '04x') + format(value2, '04x')
    ladung = int(struct.unpack('>i', all.decode('hex'))[0])
    resp= client.read_holding_registers(31395,2,unit=3)
    value1 = resp.registers[0]
    value2 = resp.registers[1]
    all = format(value1, '04x') + format(value2, '04x')
    entladung = int(struct.unpack('>i', all.decode('hex'))[0])
    if ladung > 5:
        final=ladung
    else:
        final=entladung * -1
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/power", final)

    simcount.sim_count(final, "openWB/set/bat/"+str(bat_num)+"/", bat.data["set"])
