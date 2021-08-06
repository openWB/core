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
    val =  addr
    if val > 32767:
        val -= 65535
    return val

def read_solax(pv):
    pv_num = pv.pv_num
    ipaddress = pv.data["config"]["config"]["solax"]["ip_address"]

    client = ModbusTcpClient(ipaddress, port=502)

    resp=client.read_input_registers(10, 2)
    pv1 = unsigned16(resp, 0)
    pv2 = unsigned16(resp, 1)
     # Erzeugung negativ  
    pub.pub("openWB/set/pv/"+str(pv_num)+"/get/power", (pv1 + pv2) * -1)

    resp=client.read_input_registers(80, 4)
    pvtoday = unsigned32(resp,0) / 10   # yield today
    pub.pub("openWB/set/pv/"+str(pv_num)+"/get/daily_yield", pvtoday)
    pvall = unsigned32(resp,2)       # yield overall
    pub.pub("openWB/set/pv/"+str(pv_num)+"/get/counter", pvall)

    client.close()
