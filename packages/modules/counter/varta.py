import struct
from pymodbus.client.sync import ModbusTcpClient

from ...helpermodules import pub
from ...helpermodules import simcount

def read_varta(counter):
    counter_num = counter.counter_num
    ipaddress = counter.data["config"]["config"]["varta"]["ip_address"]
    client = ModbusTcpClient(ipaddress, port=502)

    # gridleistung
    resp= client.read_holding_registers(1078,1,unit=1)
    value1 = resp.registers[0]
    all = format(value1, '04x')
    final = int(struct.unpack('>h', all.decode('hex'))[0])*-1 
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_all", final)

    simcount.sim_count(final, "openWB/set/counter/"+str(counter_num)+"/", counter.data["set"])

