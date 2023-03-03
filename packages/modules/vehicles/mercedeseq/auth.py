#!/usr/bin/python3

import json
import pathlib
import sys
import time
import html
import paho.mqtt.subscribe as subscribe
import paho.mqtt.publish as publish

sys.path.append(str(pathlib.Path(__file__).resolve().parents[3]))
from modules.common import req  # noqa: E402

# call parameters
ev_id = sys.argv[1]
code = sys.argv[2]
callback = sys.argv[3]


def printDebug(message, level):
    html_message = html.escape(message)
    if level >= debug:
        print("<p>" + html_message + "</p>")


def printHtml(message):
    html_message = html.escape(message)
    print("<p>" + html_message + "</p>")


msg = subscribe.simple("openWB/system/debug_level", hostname="localhost")
debug = int(msg.payload.decode("UTF-8"))
printHtml("Debug: " + str(debug))
msg = subscribe.simple("openWB/vehicle/" + ev_id + "/soc_module/config", hostname="localhost")
conf = json.loads(msg.payload)


client_id = conf['configuration']['client_id']
client_secret = conf['configuration']['client_secret']

printDebug("ClientID:"+client_id[0:3] + "**********" + client_id[-3:0], 10)
printDebug("ClientSecret: " + client_secret[0:3] + "**********" + client_secret[-3:], 10)
printDebug("Callback:" + callback, 10)

tok_url = "https://ssoalpha.dvb.corpinter.net/v1/token"

data = {'grant_type': 'authorization_code', 'code': str(code), 'redirect_uri': callback}
# call API to get Access/Refresh tokens
act = req.get_http_session().post(tok_url, data=data, verify=True,
                                  allow_redirects=False, auth=(client_id, client_secret))

printDebug(act.url, 20)

if act.status_code == 200:
    # valid Response
    tokens = json.loads(act.text)
    access_token = tokens['access_token']
    refresh_token = tokens['refresh_token']
    expires_in = int(time.time())
    token_type = tokens['token_type']
    id_token = tokens['id_token']

    # persist tokens
    conf['configuration']['token']['refresh_token'] = refresh_token
    conf['configuration']['token']['access_token'] = access_token
    conf['configuration']['token']['expires_in'] = expires_in
    conf['configuration']['token']['id_token'] = id_token
    conf['configuration']['token']['token_type'] = token_type
    printDebug(str(conf), 10)
    publish.single("openWB/set/vehicle/" + ev_id +
                   "/soc_module/config", json.dumps(conf), retain=True, hostname="localhost")

    printHtml("Anmeldung erfolgreich!")
    print("<a href=""javascript:window.close()"">Sie können das Fenster schließen.</a>")
else:
    printHtml("Anmeldung Fehlgeschlagen Code: " + str(act.status_code) + " " + act.text)
    printHtml("Code: " + code + " ev_id: " + ev_id)
