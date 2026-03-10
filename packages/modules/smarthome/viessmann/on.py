#!/usr/bin/python3
import sys
from pymodbus.client.sync import ModbusTcpClient
import logging

log = logging.getLogger(__name__)

devicenumber = str(sys.argv[1])
ipadr = str(sys.argv[2])
uberschuss = int(sys.argv[3])
# standard
# lesen
# own log
# Anzeige und Einstellung der Komfortfunktion "Einmalige Warmwasserbereitung"
# ausserhalb des Zeitprogramms:
# 0: "Einmalige Warmwasserbereitung" AUS
# 1: "Einmalige Warmwasserbereitung" EIN
# Fuer die "Einmalige Warmwasserbereitung" wird der Warmwassertemperatur-Sollwert 2 genutzt.
# CO-17
# coils read write boolean
# register start 00000
#
log.debug(
    f"[Viessmann {devicenumber}] devicenr {devicenumber} ipadr {ipadr} "
    f"ueberschuss {uberschuss:6d} try to connect (modbus)")
client = ModbusTcpClient(ipadr, port=502)
rq = client.write_coil(16, True, unit=1)
log.debug(f"[Viessmann {devicenumber}] Modbus write_coil response: {rq}")
client.close()
log.debug(
    f"[Viessmann {devicenumber}] devicenr {devicenumber} ipadr {ipadr} "
    "Einmalige Warmwasseraufbereitung aktiviert CO-17 = 1")
log.debug(f"[Viessmann {devicenumber}] PV-Modus gesetzt: 1")
with open('/var/www/html/openWB/ramdisk/smarthome_device_' + str(devicenumber) + '_pv', 'w') as f:
    f.write(str(1))
