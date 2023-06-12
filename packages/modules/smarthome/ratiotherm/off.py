#!/usr/bin/python3
import os
import sys
import logging

log = logging.getLogger("ratiotherm")
bp = '/var/www/html/openWB/ramdisk/smarthome_device_'

devicenumber = int(sys.argv[1])
ipadr = str(sys.argv[2])
uberschuss = int(sys.argv[3])
# standard
file_stringpv = bp + str(devicenumber) + '_pv'
file_stringcount = bp + str(devicenumber) + '_count'
aktpower = 0
log.info(" off devicenr %d ipadr %s ueberschuss %6d Akt Leistung  %6d"
         % (devicenumber, ipadr, uberschuss, aktpower))
pvmodus = 0
if os.path.isfile(file_stringpv):
    with open(file_stringpv, 'r') as f:
        pvmodus = int(f.read())
# wenn vorher PV-Modus an, dann watt.py
# signalisieren einmalig 0 ueberschuss zu schicken
if pvmodus == 1:
    pvmodus = 99
with open(file_stringpv, 'w') as f:
    f.write(str(pvmodus))
count1 = 999
with open(file_stringcount, 'w') as f:
    f.write(str(count1))
