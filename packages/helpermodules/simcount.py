""" Sim Count
Berechnet die importierte und exportierte Leistung, wenn der Zähler / PV-Modul / Speicher diese nicht liefert.
"""
import time

from ..helpermodules import pub


def sim_count(present_power_all, topic, data):
    """ emulate import export

    Parameters
    ----------
    present_power_all: float
        aktuelle Leistung
    topic: str "openWB/set/counter/0/"
        Topic, an das gepublished werden soll
    data:  data.data.counter_data[item].data["set"]
        Daten aus dem data-Modul auf die lesen zugegriffen wird.
    """
    sim_timestamp = time.time()
    watt1 = 0
    seconds1 = 0.0
    if "sim_timestamp" in data:
        seconds1 = float(data["sim_timestamp"])
        watt1 = int(data["present_power_all"])
        if "present_imported" in data:
            wattposh = int(data["present_imported"])
        else:
            wattposh = 0
        if "present_exported" in data:
            wattnegh = int(data["present_exported"])
        else:
            wattnegh = 0
        value1 = "%22.6f" % sim_timestamp
        pub.pub(topic+"set/sim_timestamp", value1)
        pub.pub(topic+"set/present_power_all", present_power_all)
        seconds1 = seconds1+1
        deltasec = sim_timestamp - seconds1
        deltasectrun = int(deltasec * 1000) / 1000
        stepsize = int((present_power_all-watt1)/deltasec)
        while seconds1 <= sim_timestamp:
            if watt1 < 0:
                wattnegh = wattnegh + watt1
            else:
                wattposh = wattposh + watt1
            watt1 = watt1 + stepsize
            if stepsize < 0:
                watt1 = max(watt1, present_power_all)
            else:
                watt1 = min(watt1, present_power_all)
            seconds1 = seconds1 + 1
        rest = deltasec - deltasectrun
        seconds1 = seconds1 - 1 + rest
        if rest > 0:
            watt1 = int(watt1 * rest)
            if watt1 < 0:
                wattnegh = wattnegh + watt1
            else:
                wattposh = wattposh + watt1
        wattposkh = wattposh/3600
        wattnegkh = (wattnegh*-1)/3600
        pub.pub(topic+"set/present_imported", wattposh)
        pub.pub(topic+"set/present_exported", wattnegh)
        pub.pub(topic+"get/imported", wattposkh)
        pub.pub(topic+"get/exported", wattnegkh)
    else:
        value1 = "%22.6f" % sim_timestamp
        pub.pub(topic+"set/sim_timestamp", value1)
        pub.pub(topic+"set/present_power_all", present_power_all)
