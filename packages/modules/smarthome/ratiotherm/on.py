#!/usr/bin/python3
import sys
import logging

log = logging.getLogger("ratiotherm")
bp = '/var/www/html/openWB/ramdisk/smarthome_device_'

devicenumber = int(sys.argv[1])
ipadr = str(sys.argv[2])
uberschuss = int(sys.argv[3])
# standard
# lesen
# own log
file_stringpv = bp + str(devicenumber) + '_pv'
file_stringcount = bp + str(devicenumber) + '_count'
aktpower = 0
log.info(" on devicenr %d ipadr %s ueberschuss %6d Akt Leistung  %6d"
         % (devicenumber, ipadr, uberschuss, aktpower))
with open(file_stringpv, 'w') as f:
    f.write(str(1))
count1 = 999
with open(file_stringcount, 'w') as f:
    f.write(str(count1))
