import struct
from pymodbus.client.sync import ModbusTcpClient

from ...helpermodules import pub
from ...helpermodules import simcount

def read_sungrow(counter):
    counter_num = counter.counter_num
    ipaddress = counter.data["config"]["config"]["sungrow"]["ip_address"]
    srmode = counter.data["config"]["config"]["sungrow"]["variant"]

    client = ModbusTcpClient(ipaddress, port=502)

    if srmode == 1:
        resp= client.read_input_registers(5082,2,unit=1)
        value1 = resp.registers[0]
        value2 = resp.registers[1]
        all = format(value2, '04x') + format(value1, '04x')
        final = int(struct.unpack('>i', all.decode('hex'))[0])
    else:
        resp= client.read_input_registers(13009,2,unit=1)
        value1 = resp.registers[0]
        value2 = resp.registers[1]
        all = format(value2, '04x') + format(value1, '04x')
        final = int(struct.unpack('>i', all.decode('hex'))[0]*-1)

    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_all", final)

    simcount.sim_count(final, "openWB/set/counter/"+str(counter_num)+"/", counter.data["set"])
