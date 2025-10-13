#!/usr/bin/python3

import sys
import os
import json
import logging

log = logging.getLogger(__name__)

devicenumber = str(sys.argv[1])
ipadr = str(sys.argv[2])
uberschuss = int(sys.argv[3])
file_stringpv = f'/var/www/html/openWB/ramdisk/smarthome_device_{devicenumber}_pv'
# PV-Modus
pvmodus = 0
if os.path.isfile(file_stringpv):
    with open(file_stringpv, 'r') as f:
        pvmodus = int(f.read())
aktpower = 0
powerc = 0
answer = {"power": aktpower, "powerc": powerc, "on": pvmodus}
outfile = f'/var/www/html/openWB/ramdisk/smarthome_device_ret{devicenumber}'
with open(outfile, 'w') as f1:
    json.dump(answer, f1)
