#!/usr/bin/python3

import requests
import json
import sys
import time
import html
import paho.mqtt.subscribe as subscribe
import paho.mqtt.publish as publish
sys.path.append("../../../")

# call parameters
EVId = str(sys.argv[1])
code = str(sys.argv[2])

moddir = '/var/www/html/openWB/packages/modules/vehicles/mercedeseq/'


def printDebug(message, level):
    htmlmsg = html.escape(message)
    if level >= Debug:
        print("<p>" + htmlmsg + "</p>")


def printHtml(message):
    htmlmsg = html.escape(message)
    print("<p>" + htmlmsg + "</p>")


print("<html>")

msg = (subscribe.simple("openWB/system/debug_level", hostname="localhost"))
Debug = int(str(msg.payload.decode("UTF-8")))
printHtml("Debug: " + str(Debug))
msg = subscribe.simple("openWB/vehicle/" + EVId + "/soc_module/config", hostname="localhost")
conf=json.loads(msg.payload)


client_id = conf['configuration']['client_id']
client_secret = conf['configuration']['client_secret']
callback = conf['configuration']['callbackurl']
printDebug("ClientID:"+client_id[0:3] + "**********" + client_id[-3:0],10)
printDebug("ClientSecret: " + client_secret[0:3] + "**********" + client_secret[-3:],10)
printDebug("Callback:" + callback,10)

tok_url  = "https://ssoalpha.dvb.corpinter.net/v1/token"

data = {'grant_type': 'authorization_code', 'code': str(code), 'redirect_uri': callback}
# call API to get Access/Refresh tokens
act = requests.post(tok_url, data=data, verify=True, allow_redirects=False, auth=(client_id, client_secret))

printDebug(act.url,20)

if act.status_code == 200:
    # valid Response
    toks = json.loads(act.text)
    access_token = toks['access_token']
    refresh_token = toks['refresh_token']
    expires_in = int(time.time())
    token_type = toks['token_type']
    id_token = toks['id_token']

	# persist tokens
    conf['configuration']['token']['refresh_token'] = refresh_token
    conf['configuration']['token']['access_token'] = access_token
    conf['configuration']['token']['expires_in'] = expires_in
    conf['configuration']['token']['id_token'] = id_token
    conf['configuration']['token']['token_type'] = token_type
    printDebug(str(conf),10)
    publish.single("openWB/set/vehicle/" + EVId + "/soc_module/config", json.dumps(conf),retain=True, hostname="localhost")

if act.status_code == 200:
    printHtml("Anmeldung erfolgreich!")
    print("<a href=""javascript:window.close()"">Sie k&ouml;nnen das Fenster schlie&szlig;en.</a>")
else:
    printHtml("Anmeldung Fehlgeschlagen Code: " + str(act.status_code) + " " + act.text)
    printHtml("Code: "+ code + " EVId: " + EVId)
print("</html>")
