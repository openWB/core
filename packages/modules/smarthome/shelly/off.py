#!/usr/bin/python3
import sys
from logging import exception

import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
import os
import json
import logging

log = logging.getLogger(__name__)
devicenumber = str(sys.argv[1])
ipadr = str(sys.argv[2])
uberschuss = int(sys.argv[3])
gen = '1'
model = '???'
try:
    chan = int(sys.argv[4])
except Exception:
    chan = 0
shaut = int(sys.argv[5])
user = str(sys.argv[6])
pw = str(sys.argv[7])

fbase = '/var/www/html/openWB/ramdisk/smarthome_device_ret.'
fnameg = fbase + str(ipadr) + '_shelly_infogv2'
log_pfx = "Device " + str(devicenumber) + " IP " + ipadr + ": "

try:
    if os.path.isfile(fnameg):
        with open(fnameg, 'r') as f:
            jsonin = json.loads(f.read())
            gen = str(jsonin['gen'])
            model = str(jsonin['model'])
    else:
        gen = "1"

    if gen == "1":
        if chan == 0:
            url = f"http://{ipadr}/relay/0?turn=off"
        else:
            chan = chan - 1
            url = f"http://{ipadr}/relay/{chan}?turn=off"
    else:
        if chan > 0:
            chan = chan - 1
        if "SPEM-003CE" in model:
            chan = 100
        url = f"http://{ipadr}/rpc/Switch.Set?id={chan}&on=false"

    if shaut == 1:
        if gen == "1":
            # HTTP Basic Auth für Gen 1
            auth = HTTPBasicAuth(user, pw)
        else:
            # HTTP Digest Auth für Gen 2 oder SPEM-003CE
            auth = HTTPDigestAuth("admin", pw)
        response = requests.get(url, auth=auth, timeout=3)
    else:
        response = requests.get(url, timeout=3)

    response.raise_for_status()  # Fehler, wenn Statuscode nicht 2xx ist
except Exception as e:
    log.error(f"{log_pfx}Error on changing switch: {str(e)}")
