import struct
from pymodbus.client.sync import ModbusTcpClient

from ...helpermodules import pub

def read_ethsdm120(pv):
    pv_num = pv.pv_num

    seradd = pv.data["config"]["config"]["ethsdm120"]["ip_address"]
    sdmid = pv.data["config"]["config"]["ethsdm120"]["id"]

    client = ModbusTcpClient(seradd, port=8899)

    resp = client.read_input_registers(0x0006,2, unit=sdmid)
    al1 = struct.unpack('>f',struct.pack('>HH',*resp.registers))
    al1 = float("%.3f" % al1[0])
    pub.pub("openWB/set/pv/"+str(pv_num)+"/get/current", [al1])

    resp = client.read_input_registers(0x000C,2, unit=sdmid)
    watt = struct.unpack('>f',struct.pack('>HH',*resp.registers))
    watt = int(watt[0])
    pub.pub("openWB/set/pv/"+str(pv_num)+"/get/power", watt)

    resp = client.read_input_registers(0x004a,2, unit=sdmid)
    vwh = struct.unpack('>f',struct.pack('>HH',*resp.registers))
    vwh1 = float("%.3f" % vwh[0])
    vwh2 = float(vwh1) * int(1000)
    pub.pub("openWB/set/pv/"+str(pv_num)+"/get/counter", vwh2)
