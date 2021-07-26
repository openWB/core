import struct
from pymodbus.client.sync import ModbusTcpClient

from ...helpermodules import pub
from ...helpermodules import simcount

def read_powerdog(pv):
    pv_num = pv.pv_num
    ipaddress = pv.data["config"]["config"]["powerdog"]["ip_address"]

    client = ModbusTcpClient(ipaddress, port=502)

    # evu punkt
    resp = client.read_input_registers(40002,2, unit=1)
    all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
    finaleinspeisung = int(struct.unpack('>i', all.decode('hex'))[0])
    gridw= finaleinspeisung * -1
    pub.pub("openWB/set/pv/"+str(pv_num)+"/get/power", gridw)

    simcount.sim_count(gridw, "openWB/set/pv/"+str(pv_num)+"/", pv.data["set"])