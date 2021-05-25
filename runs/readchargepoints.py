import paho.mqtt.client as mqtt
import paho.mqtt.subscribe as subscribe
import paho.mqtt.publish as publish
from subprocess import Popen
import os
import sys
import subprocess
import time
import fileinput
from datetime import datetime
import configparser
import re
import json
from threading import Thread
log_dict= {}
mqtt_broker_ip = "localhost"

try:
    with open('/var/www/html/openWB/ramdisk/ipaddress','r') as f:
        myipaddress = str(f.read())
except:
    myipaddress="192.168.193.5"
def getserial():
    with open('/proc/cpuinfo','r') as f:
        for line in f:
            if line[0:6] == 'Serial':
                return line[10:26]
        return "0000000000000000"
client = mqtt.Client("openWB-readchargepoint-" + getserial())
def readexternal_openwb(localchargepoint, ip, remotechargepoint):
    try:
        publish.single("openWB/set/isss/heartbeat", "0", hostname=ip)
        publish.single("openWB/set/isss/parentWB", str(myipaddress), hostname=ip)
        if (remotechargepoint == 2):
            publish.single("openWB/set/isss/parentCPlp2", str(localchargepoint), hostname=ip)
        else:
            publish.single("openWB/set/isss/parentCPlp1", str(localchargepoint), hostname=ip)
        #Handled in set-current.sh
        #phases_to_use=subscribe.simple("openWB/chargepoint/"+str(localchargepoint)+"/set/phases_to_use", hostname="localhost").payload.decode("utf-8")
        #publish.single("openWB/set/isss/U1p3p", str(phases_to_use), hostname=ip)
        log_dict.update({str(localchargepoint) : "No Error"})

    except Exception as e:
        log_dict.update({str(localchargepoint) : "Error reading chargepoint: "+str(e)})



def on_connectlocal(client, userdata, flags, rc):
    #subscribe to config topic for all chargepoints
    client.subscribe("openWB/chargepoint/+/config/connection_module/selected", 2)

def on_messagelocal(client, userdata, msg):
    if (len(msg.payload.decode("utf-8")) >= 1):
        devicenumb=re.sub(r'\D', '', msg.topic)
        try:
            chargepointconfig = json.loads(msg.payload.decode("utf-8"))
            if ( chargepointconfig['selected'] == "external_openwb" ):
                log_dict.update({str(devicenumb) : "Error reading chargepoint"})
                background_thread = Thread(target=readexternal_openwb, args=(int(devicenumb), str(chargepointconfig['config']['ip']), int(chargepointconfig['config']['chargepoint'])))
                background_thread.start()
        except Exception as e:
            print(str(e))



client.on_connect = on_connectlocal
client.on_message = on_messagelocal

client.connect(mqtt_broker_ip, 1883)
client.loop(timeout=5.0)
client.loop_start()

time.sleep(8)
for key in log_dict:
    if log_dict[key] == "No Error":
        publish.single("openWB/set/chargepoint/"+str(key)+"/get/fault_state", "0", hostname="localhost")
    else:
        publish.single("openWB/set/chargepoint/"+str(key)+"/get/fault_state", "1", hostname="localhost")
    publish.single("openWB/set/chargepoint/"+str(key)+"/get/fault_str", str(log_dict[key]), hostname="localhost")
client.disconnect()


