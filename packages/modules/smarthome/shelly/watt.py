#!/usr/bin/python3
import sys
import os
import time
import json
import urllib.request
from typing import Any
from smarthome.smartret import writeret
import logging

log = logging.getLogger(__name__)

def totalPowerFromShellyJson(answer: Any, workchan: int, component: str, count: int) -> int:
    if (workchan == 0):
        power_sum = sum(emeter['power'] for emeter in answer[component] if isinstance(emeter, dict) and 'power' in emeter)
        return int(power_sum)
    return int(answer[component][workchan-1]['power'])

named_tuple = time.localtime()   # getstruct_time
time_string = time.strftime("%m/%d/%Y, %H:%M:%S shelly watty.py", named_tuple)
devicenumber = int(sys.argv[1])
ipadr = str(sys.argv[2])
uberschuss = int(sys.argv[3])
try:
    chan = int(sys.argv[4])
except Exception:
    chan = 0
# chan = 0 alle Meter, Kan 0
# chan = 1 meter 1, Kan 0
# chan = 2 meter 2, kan 1
shaut = int(sys.argv[5])
user = str(sys.argv[6])
pw = str(sys.argv[7])
# Setze Default-Werte, andernfalls wird der letzte Wert ewig fortgeschrieben.
# Insbesondere wichtig für aktuelle Leistung
# Zähler wird beim Neustart auf 0 gesetzt, darf daher nicht übergeben werden.
powerc = 0
temp = [ '0.0', '0.0', '0.0' ]
aktpower = 0
relais = 0
gen = '1'
model = '???'
# Shelly 3EM kennt die Profile monophase & triphase:
profile = '???'
components = {}
# lesen endpoint, gen bestimmem. gen 1 hat unter Umstaenden keinen Eintrag
write_info = False
delete_info = False
device_info = {}
power_field = [ 'total_act_power', 'a_act_power', 'b_act_power', 'c_act_power' ]

fbase = '/var/www/html/openWB/ramdisk/smarthome_device_ret.'
fname = fbase + str(ipadr) + '_shelly_info'
fnameg = fbase + str(ipadr) + '_shelly_infogv2'
fnamec = fbase + str(ipadr) + '_shelly_infoc'
if os.path.isfile(fnameg):
    try:
        with open(fnameg, 'r') as f:
            device_info = json.loads(f.read())
            gen = str(device_info['gen'])
            model = str(device_info['model'])
            profile = str(device_info['profile'])
            components = str(device_info['components'])
    except Exception:
        delete_info = True
        pass
else:
    aread = urllib.request.urlopen("http://" + str(ipadr) + "/shelly",
                                   timeout=3).read().decode("utf-8")
    agen = json.loads(str(aread))
    with open(fname, 'w') as f:
        json.dump(agen, f)
    if 'gen' in agen:
        gen = str(int(agen['gen']))
    device_info['gen'] = gen
    if 'model' in agen:
        model = str(agen['model'])
    elif 'type' in agen:
        model = str(agen['type'])
    device_info['model'] = model
    if 'profile' in agen:
        # Shelly mit mehreren Profilen (z.B. 3EM, 2PM)
        profile = str(agen['profile'])
        device_info['profile'] = profile
        if gen != "1":
            aread = urllib.request.urlopen("http://" + str(ipadr) + "/rpc/Shelly.ListProfiles",
                                       timeout=3).read().decode("utf-8")
            agen = json.loads(str(aread))
            with open(fnamec, 'w') as f:
                json.dump(agen, f)
            for item in agen['profiles'][profile]['components']:
                components[item['type']] = item['count']
            device_info['components'] = components

    write_info = True

# Versuche Daten von Shelly abzurufen.
try:
    # print("Shelly " + str(shaut) + user + pw)
    if gen == "1":
        url = "http://" + str(ipadr) + "/status"
        if (shaut == 1):
            passman = urllib.request.HTTPPasswordMgrWithDefaultRealm()
            passman.add_password(None, url, user, pw)
            authhandler = urllib.request.HTTPBasicAuthHandler(passman)
            opener = urllib.request.build_opener(authhandler)
            urllib.request.install_opener(opener)
        with urllib.request.urlopen(url, timeout=3) as response:
            aread = response.read().decode("utf-8")
        answer = json.loads(str(aread))
    else:
        aread = urllib.request.urlopen("http://"+str(ipadr) +
                                       "/rpc/Shelly.GetStatus",
                                       timeout=3).read().decode("utf-8")
        answer = json.loads(str(aread))
    with open('/var/www/html/openWB/ramdisk/smarthome_device_ret.' +
              str(ipadr) + '_shelly', 'w') as f:
        f.write(str(answer))
    if not components:
        # Gen2+ - Komponenten:
        prefixes = ["switch:", "em:", "emdata:", "pm1:", "em1:", "em1data:", "temperature:"]
        components = {
            prefix[:-1]: count  # Entfernt ":" für den Schlüssel (z. B. "switch:" -> "switch")
            for prefix in prefixes
            if (count := sum(key.startswith(prefix) for key in answer.keys())) > 0
        }
        # Gen1 - Komponenten:
        prefixes = ["relays", "emeters", "meters", "ext_temperature"]
        for prefix in prefixes:
            if prefix in answer:
                components[prefix] = len(answer.get(prefix))
        device_info['components'] = components

except Exception as e:
    print ("Fehler" + str(e))
    log.debug("failed to connect to device on " +
              ipadr + ", setting all values to 0")
#  answer.update(a_dictionary)
#  Versuche Werte aus der Antwort zu extrahieren.
except Exception:
    pass

        # shelly pro 3em mit add on hat fix id 100 als switch Kanal, das Device muss auf jeden fall mit separater
        # Leistungsmessung erfasst werden, da die Leistung auf drei verschieden Kanäle angeliefert werden kann
#        if ("SPEM-003CE" in model):
#            workchan = 100
#        sw = 'switch:' + str(workchan)
#        relais = int(answer[sw]['output'])

workchan = chan - 1 if chan > 0 else chan

if 'switch' in components:
    sw = 'switch:'+str(workchan)
    if not sw in answer:
        sw = 'switch:0'
    relais = int(answer[sw]['output'])
    aktpower = int(answer[sw]['apower']) if 'apower' in answer[sw] else 0
if 'relays' in components:
    relais = int(answer['relays'][workchan if (workchan < len(answer['relays'])) else 0]['ison'])
if 'meters' in components:
    aktpower = totalPowerFromShellyJson(answer, chan, 'meters', components['meters'])
if 'pm1' in components:
    sw = 'pm1:'+str(workchan)
    aktpower = int(answer[sw]['apower'])
if 'em1' in components:
    if (workchan == 0):
        aktpower = int(sum(answer['em1:'+str(em)]['act_power'] for em in range(components['em1'])))
    else:
        sw = 'em1:'+str(workchan)
        aktpower = int(answer[sw]['act_power'])
if 'em' in components:
    aktpower = int(answer['em:0'][power_field[chan]])
if 'emeters' in components:
    aktpower = totalPowerFromShellyJson(answer, chan, 'emeters', components['emeters'])

if 'ext_temperature' in components:
    for i in range(len(answer['ext_temperature'])):
        temp[i] = str(answer['ext_temperature'][str(i)]['tC'])
if 'temperature' in components:
    for i in range(components['temperature']):
        field = 'temperature:' + str(i+100)
        if field in answer:
            temp[i] = str(answer[field]['tC'])

if write_info:
    with open(fnameg, 'w') as f:
        f.write(json.dumps(device_info))

if delete_info:
    try:
        os.remove(fname)
    except Exception:
        pass

answer = '{"power":' + str(aktpower) + ',"powerc":' + str(powerc)
answer += ',"on":' + str(relais) + ',"temp0":' + str(temp[0])
answer += ',"temp1":' + str(temp[1]) + ',"temp2":' + str(temp[2]) + '}'
writeret(answer, devicenumber)
print ("Answer: " + answer)
