from pymodbus.client.sync import ModbusTcpClient

from ...helpermodules import pub

def read_saxpower(bat):
    bat_num = bat.bat_num
    ipaddress = bat.data["config"]["config"]["saxpower"]["ip_address"]

    client = ModbusTcpClient(ipaddress, port=3600)

    # Register auslesen
    resp= client.read_holding_registers(46, 2,unit=64)

    # SOC
    soc = resp.registers[0]
    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/soc", soc)

    # akt. Speicherleistung
    sax_pow=resp.registers[1]
    # unsigned to signed int
    if sax_pow > 32767:
        sax_pow -= 65535

    # Entladen: negativ
    # Laden: positiv
    sax_pow *=-1

    pub.pub("openWB/set/bat/"+str(bat_num)+"/get/power", sax_pow)
