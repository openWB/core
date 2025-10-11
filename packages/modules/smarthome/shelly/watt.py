#!/usr/bin/python3
import sys
import os
import time
import json
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
from typing import Any
from smarthome.smartret import writeret
import logging

log = logging.getLogger(__name__)

def totalPowerFromShellyJson(answer: Any, workchan: int, component: str) -> int:
    if workchan > 0:
        return int(answer[component][workchan - 1]['power'])
    power_sum = sum(emeter['power'] for emeter in answer[component] if isinstance(emeter, dict) and 'power' in emeter)
    return int(power_sum)

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
powerc = 0
temp = ['0.0', '0.0', '0.0']
aktpower = 0
relais = 0
gen = '1'
model = '???'
profile = '???'
components = {}
# lesen endpoint, gen bestimmem. gen 1 hat unter Umstaenden keinen Eintrag
write_info = False
delete_info = False
device_info = {}
power_field = ['total_act_power', 'a_act_power', 'b_act_power', 'c_act_power']

fbase = '/var/www/html/openWB/ramdisk/smarthome_device_ret.'
# Response of "/shelly"-url:
fname_shellyinfo = fbase + ipadr + '_shelly_info'
# Response of "/rpc/Shelly.ListProfiles":
fname_profiles = fbase + ipadr + '_shelly_infoc'
# Internal cache for gathered device info:
fname_devcache = fbase + ipadr + '_shelly_infogv2'
# Response for "/status" or "/rpc/Shelly.GetStatus":
fname_statusrsp = fbase + ipadr + '_shelly_res'

log_pfx = "Device " + str(devicenumber) + " IP " + ipadr + ": "

# Do we have a cache of the device features?
try:
    if os.path.isfile(fname_devcache):
        try:
            with open(fname_devcache, 'r') as f:
                device_info = json.loads(f.read())
                gen = str(device_info['gen'])
                model = str(device_info['model'])
                profile = str(device_info['profile'])
                components = device_info['components']  # Kein str(), da dict
        except Exception:
            # Delete this cache file - it seems broken
            delete_info = True
            pass
    else:
        # New device analysis: Start with /shelly URL
        url = f'http://{ipadr}/shelly'
        response = requests.get(url, timeout=3)
        response.raise_for_status()
        aread = response.text
        log.warning(log_pfx + "/shelly response " + aread)
        device_info = json.loads(aread)
        agen = json.loads(aread)
        with open(fname_shellyinfo, 'w') as f:
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
            # Shelly with multiple profiles (z.B. 3EM, 2PM)
            profile = str(agen['profile'])
            device_info['profile'] = profile
            if gen != "1":
                url = f'http://{ipadr}/rpc/Shelly.ListProfiles'
                if shaut==1:
                    response = requests.get(url, timeout=3,
                                            auth=HTTPDigestAuth("admin", pw))
                else:
                    response = requests.get(url, timeout=3)
                response.raise_for_status()
                aread = response.text
                log.warning(log_pfx + " /rpc/Shelly.ListProfiles response " + aread)
                agen = json.loads(aread)
                with open(fname_profiles, 'w') as f:
                    json.dump(agen, f)
                for item in agen['profiles'][profile]['components']:
                    components[item['type']] = item['count']
                device_info['components'] = components
        # We have a new device analysis, store it:
        write_info = True
except Exception as e:
    log.error(log_pfx + 'Error on device analysis ' + str(e))
    pass

# Pre-Analysis done / loaded, now get the data:
try:
    # For future use: Caching of response:
    # Check the last response is < 5 seconds old
    if (os.path.exists(fname_statusrsp) and
            os.path.getmtime(fname_statusrsp) + 4 > time.time()):
        # We will use a cached Status-page
        with open(fname_statusrsp, 'r') as f:
            answer = json.loads(f.read())
    else:
        # No (valid) cache: We have to fetch the data:
        url = f'http://{ipadr}/{"status" if gen == "1" else "rpc/Shelly.GetStatus"}'
        if shaut == 1:
            if gen == "1":
                response = requests.get(url, timeout=3,
                                    auth=HTTPBasicAuth(user, pw))
            else:
                response = requests.get(url, timeout=3,
                                    auth=HTTPDigestAuth("admin", pw))
        else:
            response = requests.get(url, timeout=3)

        response.raise_for_status()
        aread = response.text
        answer = json.loads(aread)
        with open(fname_statusrsp, 'w') as f:
            json.dump(answer, f)

    if not components:
        # Late device analysis, based on the first response:
        prefixes = ['switch:', 'em:', 'emdata:', 'pm1:', 'em1:', 'em1data:', 'temperature:']
        components = {
            prefix[:-1]: count
            for prefix in prefixes
            if (count := sum(key.startswith(prefix) for key in answer.keys())) > 0
        }
        # Gen1 - Komponenten:
        prefixes = ['relays', 'emeters', 'meters', 'ext_temperature']
        for prefix in prefixes:
            if prefix in answer:
                components[prefix] = len(answer.get(prefix))
        device_info['components'] = components
        write_info = True

except Exception as e:
    log.error(log_pfx + 'Error on data fetch ' + str(e))
    pass

# We have the response: Start parsing:
workchan = chan - 1 if chan > 0 else chan

try:
    if 'switch' in components:
        # Beim Shelly Pro 3EM mit AddOn ist die Switch-ID 100, sonst ab 0:
        sw = 'switch:' + str(workchan) if not 'SPEM-003CE' in model else 'switch:100'
        if not sw in answer:
            # Typisch, wenn der Messwert auf einem höheren Kanal geholt werden soll
            sw = 'switch:0'
        relais = int(answer[sw]['output'])
        aktpower = int(answer[sw]['apower']) if 'apower' in answer[sw] else 0
    if 'relays' in components:
        relais = int(answer['relays'][workchan if (workchan < len(answer['relays'])) else 0]['ison'])
    if 'meters' in components:
        aktpower = totalPowerFromShellyJson(answer, chan, 'meters')
    if 'pm1' in components:
        if chan == 0:
            aktpower = int(sum(answer['pm1:' + str(em)]['apower'] for em in range(components['pm1'])))
        else:
            sw = 'pm1:' + str(workchan)
            aktpower = int(answer[sw]['apower'])
    if 'em1' in components:
        if chan == 0:
            aktpower = int(sum(answer['em1:' + str(em)]['act_power'] for em in range(components['em1'])))
        else:
            sw = 'em1:' + str(workchan)
            aktpower = int(answer[sw]['act_power'])
    if 'em' in components:
        aktpower = int(answer['em:0'][power_field[chan]])
    if 'emeters' in components:
        aktpower = totalPowerFromShellyJson(answer, chan, 'emeters')
    if 'ext_temperature' in components:
        for i in range(len(answer['ext_temperature'])):
            temp[i] = str(answer['ext_temperature'][str(i)]['tC'])
    if 'temperature' in components:
        for i in range(components['temperature']):
            field = 'temperature:' + str(i + 100)
            if field in answer:
                temp[i] = str(answer[field]['tC'])
except Exception as e:
    exc_type, exc_value, exc_traceback = sys.exc_info()
    filename = exc_traceback.tb_frame.f_code.co_filename
    line_number = exc_traceback.tb_lineno
    function_name = exc_traceback.tb_frame.f_code.co_name
    log.error(
        f"{log_pfx}Error on data parsing: {str(e)} (File: {filename}, Line: {line_number}, Function: {function_name})")

if write_info:
    with open(fname_devcache, 'w') as f:
        f.write(json.dumps(device_info))
    log.warning(log_pfx + " cached info " + json.dumps(device_info))

if delete_info:
    try:
        os.remove(fname_shellyinfo)
    except Exception:
        pass

answer = '{"power":' + str(aktpower) + ',"powerc":' + str(powerc)
answer += ',"on":' + str(relais) + ',"temp0":' + str(temp[0])
answer += ',"temp1":' + str(temp[1]) + ',"temp2":' + str(temp[2]) + '}'
writeret(answer, devicenumber)
