#!/usr/bin/python3
import logging
import sys
import json
import jq
import urllib.request

log = logging.getLogger(__name__)

devicenumber = str(sys.argv[1])
# Abfrage-URL, die die .json Antwort liefert. Z.B.
# "http://192.168.0.150/solar_api/v1/GetMeterRealtimeData.cgi?Scope=Device&DeviceID=1"
jsonurl = str(sys.argv[2])
jsonpower = str(sys.argv[3])  # json Key in dem der aktuelle Leistungswert steht, z.B. ".Body.Data.PowerReal_P_Sum"
# json Key in dem der summierte Verbrauch steht, z.B. ".Body.Data.EnergyReal_WAC_Sum_Consumed"
jsonpowerc = str(sys.argv[4])

answer = json.loads(str(urllib.request.urlopen(jsonurl, timeout=3).read().decode("utf-8")))

try:
    power = jq.compile(jsonpower).input(answer).first()
    power = int(abs(power))
except Exception:
    power = 0

try:
    powerc = jq.compile(jsonpowerc).input(answer).first()
    powerc = int(abs(powerc))
except Exception:
    powerc = 0

log.debug('Device' + str(devicenumber) + '{"power":' + str(power) + ',"powerc":' + str(powerc) + '}')
