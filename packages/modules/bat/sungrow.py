import struct
from pymodbus.client.sync import ModbusTcpClient

from ...helpermodules import pub
from ...helpermodules import simcount

def read_sungrow(bat):
    bat_num = bat.bat_num
    ipaddress = bat.data["config"]["config"]["sungrow"]["ip_address"]

    client = ModbusTcpClient(ipaddress, port=502)

    resp= client.read_input_registers(13022,1,unit=1)
    value1 = resp.registers[0]
    all = format(value1, '04x')
    final = int(struct.unpack('>h', all.decode('hex'))[0] / 10 )
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/soc", final)

    resp= client.read_input_registers(13000,1,unit=1)
    value1 = resp.registers[0]
    binary=bin(value1)[2:].zfill(8)

    # battwatt
    resp= client.read_input_registers(13021,1,unit=1)
    value1 = resp.registers[0]
    all = format(value1, '04x')
    power = int(struct.unpack('>h', all.decode('hex'))[0])
    if (binary[5] == "1"):
        power=power*-1
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/power", power)

    simcount.sim_count(power, "openWB/set/bat/"+str(bat_num)+"/", bat.data["set"])
