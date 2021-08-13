import json

from ...helpermodules import log
from ...helpermodules import pub

def read_external_openwb(cp):
    try:
        ip_address =cp.data["config"]["connection_module"]["config"]["external_openwb"]["ip_address"]
        cp_num=cp.cp_num
        duo_num=cp.data["config"]["connection_module"]["config"]["external_openwb"]["chargepoint"]
        try:
            with open('/var/www/html/openWB/ramdisk/ipaddress','r') as f:
                myipaddress = str(f.read())
        except:
            myipaddress="192.168.193.5"
        pub.pub_single("openWB/set/isss/heartbeat", json.dumps(0), hostname=ip_address)
        pub.pub_single("openWB/set/isss/parentWB", json.dumps(str(myipaddress)), hostname=ip_address)
        if (duo_num == 2):
            pub.pub_single("openWB/set/isss/parentCPlp2", json.dumps(str(cp_num)), hostname=ip_address)
        else:
            pub.pub_single("openWB/set/isss/parentCPlp1", json.dumps(str(cp_num)), hostname=ip_address)
    except Exception as e:
        log.exception_logging(e)

def write_external_openwb(ip_address, num, current):
    try:
        # Zweiter LP der Duo
        if num == 2:
            pub.pub_single("openWB/set/isss/Lp2Current", current, hostname=ip_address)
        else:
            pub.pub_single("openWB/set/isss/Current", current, hostname=ip_address)
    except Exception as e:
        log.exception_logging(e)