"""
"""
import json
import requests

from ...helpermodules import pub

def read_discovergy(counter):
    """
    Parameters
    ----------
    counter_num: int
        Nummer des Zähles
    user: str
        Benutzername
    password: str
        Passwort
    id: str
        Id des Discovergy-Zählers
    """
    counter_num = counter.counter_num
    username = counter.data["config"]["config"]["discovergy"]["username"]
    password = counter.data["config"]["config"]["discovergy"]["password"]
    id = counter.data["config"]["config"]["discovergy"]["id"]
    params = (
        ('meterId', id),
    )

    output = requests.get('https://api.discovergy.com/public/v1/last_reading', params=params, auth=(username, password), timeout = 3)
    response=json.loads(output)

    einspeisungwh = response["values"]["energyOut"] / 10000000
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/exported", einspeisungwh)

    bezugwh = response["values"]["energy"] / 10000000
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/imported", bezugwh)

    vl1=response["values"]["voltage1"] / 1000
    vl2=response["values"]["voltage2"] / 1000
    vl3=response["values"]["voltage3"] / 1000
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/voltage", [vl1, vl2, vl3])

    watt = response["values"]["power"] / 1000
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_all", watt)
    wattl1 = response["values"]["power1"] / 1000
    wattl2 = response["values"]["power2"] / 1000
    wattl3 = response["values"]["power3"] / 1000
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/power_phase", [wattl1, wattl2, wattl3])
    if vl1 > 150:
        al1 = wattl1 / vl1 
    else:
        al1 = wattl1 / 230
    if vl2 > 150:
        al2 = wattl2 / vl2
    else:
        al2 = wattl2 / 230
    if vl3 > 150:
        al3 = wattl3 / vl3
    else:
        al3 = wattl3 / 230
    pub.pub("openWB/set/counter/"+str(counter_num)+"/get/current", [al1, al2, al3])