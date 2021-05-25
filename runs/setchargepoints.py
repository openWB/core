import paho.mqtt.client as mqtt
import paho.mqtt.subscribe as subscribe
import paho.mqtt.publish as publish
import re
import json
import sys
chargepoint=sys.argv[2]
ll=sys.argv[1]

#print('cp'+str(chargepoint)+' ll: '+str(ll))
cpconfig=subscribe.simple("openWB/chargepoint/"+str(chargepoint)+"/config/connection_module/selected", hostname="localhost").payload.decode("utf-8")
chargepointconfig = json.loads(cpconfig)
if ( chargepointconfig['selected'] == "external_openwb" ):
    if ( chargepointconfig['config']['chargepoint'] == "2" ):
        publish.single("openWB/set/isss/Lp2Current", str(ll), hostname=str(chargepointconfig['config']['ip']))
    else:
        publish.single("openWB/set/isss/Current", str(ll), hostname=str(chargepointconfig['config']['ip']))



