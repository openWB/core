import struct
from pymodbus.client.sync import ModbusTcpClient

from ...helpermodules import pub
from ...helpermodules import simcount

def read_siemens(bat):
    bat_num = bat.bat_num
    ipaddress = bat.data["config"]["config"]["siemens"]["ip_address"]

    client = ModbusTcpClient(ipaddress, port=502)

    # speicherleistung
    resp= client.read_holding_registers(6,2,unit=1)
    value1 = resp.registers[0]
    value2 = resp.registers[1]
    all = format(value1, '04x') + format(value2, '04x')
    power = int(struct.unpack('>i', all.decode('hex'))[0])*-1
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/power", power)

    # soc
    resp= client.read_holding_registers(8,2,unit=1)
    value1 = resp.registers[0]
    value2 = resp.registers[1]
    all = format(value1, '04x') + format(value2, '04x')
    final = int(struct.unpack('>i', all.decode('hex'))[0])
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/soc", final)

    simcount.sim_count(power, "openWB/set/bat/"+str(bat_num)+"/", bat.data["set"])
