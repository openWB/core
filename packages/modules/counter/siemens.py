import struct
from pymodbus.client.sync import ModbusTcpClient

from ...helpermodules import pub
from ...helpermodules import simcount

def read_siemens(counter):
    counter_num = counter.counter_num
    client = ModbusTcpClient(counter.data["config"]["config"]["siemens"]["ip_address"], port=502)

    resp= client.read_holding_registers(14,2,unit=1)
    value1 = resp.registers[0]
    value2 = resp.registers[1]
    all = format(value1, '04x') + format(value2, '04x')
    final = int(struct.unpack('>i', all.decode('hex'))[0])
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_all", final)

    simcount.sim_count(final, "openWB/set/counter/"+str(counter_num)+"/", counter.data["set"])
