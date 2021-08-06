from pymodbus.client.sync import ModbusTcpClient

from ...helpermodules import pub

def unsigned32(result, addr):
   low  = result.registers[addr]
   high = result.registers[addr + 1]
   val = low +( high << 16)
   return val

def unsigned16 (result, addr):
    return result.registers[addr]

def signed16(result, addr):
    val = result.registers[addr]
    if val > 32767:
        val -= 65535
    return val

def signed32(result, addr):
    val = unsigned32(result, addr)
    if val > 2147483647:
        val -=  4294967295
    return val

def read_solax(counter):
    counter_num = counter.counter_num
    ipaddress = counter.data["config"]["config"]["solax"]["ip_address"]
    client = ModbusTcpClient(ipaddress, port=502)

    resp=client.read_input_registers(0, 114)

    value = signed32(resp, 70)
    # for SolaX negative means get power from grid
    value = -value

    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_all", value)

    frequenz = unsigned16(resp,7) / 100
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/frequency", frequenz)

    consumed = unsigned32(resp,74) / 100
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/imported", consumed)

    einspeisung = unsigned32(resp,72) / 100
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/exported", einspeisung)
