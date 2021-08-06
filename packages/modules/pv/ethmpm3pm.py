import struct
from pymodbus.client.sync import ModbusTcpClient

from ...helpermodules import pub

def read_ethmpm3pm(pv):
    if pv.data["config"]["selected"] == "openwb_evu_kit":
        ip_address = '192.168.193.15'
    elif pv.data["config"]["selected"] == "openwb_pv_kit":
        ip_address = '192.168.193.13'
    if pv.data["config"]["config"]["openwb_evu_kit"]["version"] == 0:
        _read_version0(pv, ip_address)
    elif pv.data["config"]["config"]["openwb_evu_kit"]["version"] == 1:
        _read_lovato(pv, ip_address)
    elif pv.data["config"]["config"]["openwb_evu_kit"]["version"] == 2:
        _read_sdm(pv, ip_address)

def _read_version0(pv, ip_address):
    pv_num = pv.pv_num
    client = ModbusTcpClient(ip_address, port=8899)

    resp = client.read_input_registers(0x0004,4, unit=8)
    value1 = resp.registers[0] 
    value2 = resp.registers[1] 
    all = format(value1, '04x') + format(value2, '04x')
    ikwh = int(struct.unpack('>i', all.decode('hex'))[0]) 

    # resp = client.read_input_registers(0x0004,2, unit=sdmid)
    # ikwh = resp.registers[1]
    ikwh = float(ikwh) * 10
    pub.pub("openWB/set/pv/"+str(pv_num)+"/get/counter", ikwh)

    resp = client.read_input_registers(0x0E,2, unit=8)
    lla1 = resp.registers[1]
    lla1 = float(lla1) / 100
    resp = client.read_input_registers(0x10,2, unit=8)
    lla2 = resp.registers[1]
    lla2 = float(lla2) / 100
    resp = client.read_input_registers(0x12,2, unit=8)
    lla3 = resp.registers[1]
    lla3 = float(lla3) / 100
    pub.pub("openWB/set/pv/"+str(pv_num)+"/get/current", [lla1, lla2, lla3])

    # total watt
    resp = client.read_input_registers(0x26,2, unit=8)
    value1 = resp.registers[0] 
    value2 = resp.registers[1] 
    all = format(value1, '04x') + format(value2, '04x')
    final = int(struct.unpack('>i', all.decode('hex'))[0]) / 100
    pub.pub("openWB/set/pv/"+str(pv_num)+"/get/power", final)

def _read_lovato(pv, ip_address):
    pv_num = pv.pv_num
    client = ModbusTcpClient(ip_address, port=8899)

    # Counters
    resp = client.read_input_registers(0x1a1f,2, unit=0x08)
    all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
    finalbezug1 = int(struct.unpack('>i', all.decode('hex'))[0])
    resp = client.read_input_registers(0x1a21,2, unit=0x08)
    all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
    finalbezug2 = int(struct.unpack('>i', all.decode('hex'))[0])
    if ( finalbezug1 > finalbezug2 ):
        finalbezug=finalbezug1
    else:
        finalbezug=finalbezug2
    pub.pub("openWB/set/pv/"+str(pv_num)+"/get/counter", finalbezug)

    # phasen watt
    resp = client.read_input_registers(0x0013,2, unit=0x08)
    all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
    finalw1 = int(struct.unpack('>i', all.decode('hex'))[0] / 100)

    resp = client.read_input_registers(0x0015,2, unit=0x08)
    all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
    finalw2 = int(struct.unpack('>i', all.decode('hex'))[0] / 100)
    resp = client.read_input_registers(0x0017,2, unit=0x08)
    all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
    finalw3 = int(struct.unpack('>i', all.decode('hex'))[0] / 100)

    finalw= finalw1 + finalw2 + finalw3
    if ( finalw > 10):
        finalw=finalw*-1

    # total watt
    # resp = client.read_input_registers(0x0039,2, unit=0x08)
    # all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
    # finalw = int(struct.unpack('>i', all.decode('hex'))[0] / 100)
    pub.pub("openWB/set/pv/"+str(pv_num)+"/get/power", finalw)

    # ampere
    resp = client.read_input_registers(0x0007, 2, unit=0x08)
    all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
    lla1 = float(struct.unpack('>i', all.decode('hex'))[0]) / 10000
    resp = client.read_input_registers(0x0009, 2, unit=0x08)
    all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
    lla2 = float(struct.unpack('>i', all.decode('hex'))[0]) / 10000
    resp = client.read_input_registers(0x000b, 2, unit=0x08)
    all = format(resp.registers[0], '04x') + format(resp.registers[1], '04x')
    lla3 = float(struct.unpack('>i', all.decode('hex'))[0]) / 10000
    pub.pub("openWB/set/pv/"+str(pv_num)+"/get/current", [lla1, lla2, lla3])


def _read_sdm(pv, ip_address):
    pv_num = pv.pv_num
    client = ModbusTcpClient(ip_address, port=8899)
    sdmid = 116

    # phasen watt
    resp = client.read_input_registers(0x0C,2, unit=sdmid)
    llw1 = struct.unpack('>f',struct.pack('>HH',*resp.registers))[0]
    finalw1 = int(llw1)
    resp = client.read_input_registers(0x0E,2, unit=sdmid)
    llw1 = struct.unpack('>f',struct.pack('>HH',*resp.registers))[0]
    finalw2 = int(llw1)
    resp = client.read_input_registers(0x10,2, unit=sdmid)
    llw1 = struct.unpack('>f',struct.pack('>HH',*resp.registers))[0]
    finalw3 = int(llw1)

    finalw= finalw1 + finalw2 + finalw3
    if ( finalw > 10):
        finalw=finalw*-1
    pub.pub("openWB/set/pv/"+str(pv_num)+"/get/power", finalw)

    # ampere
    resp = client.read_input_registers(0x06,2, unit=sdmid)
    lla1 = float(struct.unpack('>f',struct.pack('>HH',*resp.registers))[0])
    lla1 = float("%.1f" % lla1)
    resp = client.read_input_registers(0x08,2, unit=sdmid)
    lla1 = float(struct.unpack('>f',struct.pack('>HH',*resp.registers))[0])
    lla2 = float("%.1f" % lla1)
    resp = client.read_input_registers(0x0A,2, unit=sdmid)
    lla1 = float(struct.unpack('>f',struct.pack('>HH',*resp.registers))[0])
    lla3 = float("%.1f" % lla1)
    pub.pub("openWB/set/pv/"+str(pv_num)+"/get/current", [lla1, lla2, lla3])

    resp = client.read_input_registers(0x0156,2, unit=sdmid)
    pvkwh = struct.unpack('>f',struct.pack('>HH',*resp.registers))[0]
    pvkwh = float("%.3f" % pvkwh) / 1000
    pub.pub("openWB/set/pv/"+str(pv_num)+"/get/counter", pvkwh
    )
