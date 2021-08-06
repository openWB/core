from pymodbus.client.sync import ModbusTcpClient

from ...helpermodules import pub

def unsigned16(result, addr):
    return result.registers[addr]

def signed16(result, addr):
    val = result.registers[addr]
    if val > 32767:
        val -= 65535
    return val

def read_solax(bat):
    bat_num = bat.bat_num
    ipaddress = bat.data["config"]["config"]["solax"]["ip_address"]

    client = ModbusTcpClient(ipaddress, port=502)

    resp=client.read_input_registers(0, 114)

    # Batterie Power
    value1 = signed16(resp, 22)
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/power", value1)

    # Batterieladezustand
    value2 = unsigned16(resp, 28 )
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/soc", value2)
