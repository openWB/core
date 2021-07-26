import struct
from pymodbus.client.sync import ModbusTcpClient

from ...helpermodules import pub
from ...helpermodules import simcount

def read_sungrow(pv):
    pv_num = pv.pv_num
    ipaddress = pv.data["config"]["config"]["sungrow"]["ip_address"]

    client = ModbusTcpClient(ipaddress, port=502)

    resp= client.read_input_registers(5016,2,unit=1)
    value1 = resp.registers[0]
    value2 = resp.registers[1]
    all = format(value2, '04x') + format(value1, '04x')
    final = int(struct.unpack('>i', all.decode('hex'))[0]*-1)
    pub.pub("openWB/set/pv/"+str(pv_num)+"/get/power", final)

    simcount.sim_count(final, "openWB/set/pv/"+str(pv_num)+"/", pv.data["set"])