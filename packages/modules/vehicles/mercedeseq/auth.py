#!/usr/bin/python3

import requests, json, sys, time, os, html
sys.path.append("../../../")
from modules.common import store
#from ....dataclass_utils import asdict, dataclass_from_dict
#from ....modules.vehicles.mercedeseq.config import MercedesEQSocConfiguration
#from ....helpermodules.pub import Pub


#call parameters
EVId = str(sys.argv[1]) 
code        = str(sys.argv[2]) 
#Debug       = int(os.environ.get('debug'))
Debug       = 0

moddir = '/var/www/html/openWB/packages/modules/vehicles/mercedeseq/'


def printDebug(message, level):
    htmlmsg = html.escape(message)
    if level <= Debug:
        print("<p>" + htmlmsg + "</p>")


def printHtml(message):
    htmlmsg = html.escape(message)
    print("<p>" + htmlmsg + "</p>")

print("<html>")

#config=dataclass_from_dict(MercedesEQSocConfiguration,config)

client_id = ""
client_secret = ""
callback =""
client_id = "b85c982a-c432-4ef5-8f59-2a34d1f066d8"
client_secret = "vBKzbVeTIRuAZqxDsRawvwrFJqGZDSjYbOUlakaLugpetJTuUsTqcjQqAhcRdalH"
callback = "http://192.168.178.89/openWB/packages/modules/vehicles/mercedeseq/callback_ev.php"
            

#get last Character to identify the Chargepoint
EVId = EVId[-1]

tok_url  = "https://ssoalpha.dvb.corpinter.net/v1/token"

data = {'grant_type': 'authorization_code', 'code': str(code), 'redirect_uri': callback}
#call API to get Access/Refresh tokens
act = requests.post(tok_url, data=data, verify=True, allow_redirects=False, auth=(client_id, client_secret))

printDebug(act.url,1)

if act.status_code == 200:
  #valid Response
  toks = json.loads(act.text)
  access_token = toks['access_token']
  refresh_token = toks['refresh_token']
  expires_in = int(time.time())

	#write tokens to files

  #PUB().pub("openWB/set/vehicle/"+str(EVId)+"soc_module/config",)
  tokenfile=moddir + 'soc_eq_acc_ev' + str(EVId)
  fd = open(tokenfile,'w')
  json.dump({'expires_in' : expires_in, 'refresh_token' : refresh_token, 'access_token' : access_token}, fd)
  fd.close()
  if oct(os.stat(tokenfile).st_mode)[-3:] != "777":
    os.chmod(tokenfile,0o777)
  # ev = store.get_car_value_store(ChargePoint)


if act.status_code == 200:
    printHtml( "Anmeldung erfolgreich!" )
    print( "<a href=""javascript:window.close()"">Sie k&ouml;nnen das Fenster schlie&szlig;en.</a>" )
else: 
    printHtml("Anmeldung Fehlgeschlagen Code: " + str(act.status_code) + " " + act.text)
    printHtml("Code: "+ code + " EVId: " + EVId)
print("</html>")
