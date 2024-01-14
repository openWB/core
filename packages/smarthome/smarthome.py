#!/usr/bin/python3
import threading
from smarthome.smartcommon import mainloop, initparam
import logging
from threading import Thread
from helpermodules.subdata import SubData
log = logging.getLogger()

#
#  openwb 2.0 spec
mqttcg = 'openWB/LegacySmartHome/config/get/'
mqttcs = 'openWB/set/LegacySmartHome/config/set/'
mqttsdevstat = 'openWB/LegacySmartHome/Devices'
mqttsglobstat = 'openWB/LegacySmartHome/Status/'
mqtttopicdisengageable = 'openWB/set/counter/set/disengageable_smarthome_power'
ramdiskwrite = False
mqttport = 1886
#

bp = '/var/www/html/openWB'


def readmq() -> None:
    logging.getLogger("smarthome").setLevel(logging.DEBUG)
    log.info("*** Smarthome openWB readmq Start ***")


def smarthome_handler() -> None:
    def handler() -> None:
        try:
            try:
                speicherleistung = int(SubData.bat_all_data.data.get.power)
            except Exception:
                log.exception("Fehler beim Auslesen der Ramdisk  (Speicherleistung)")
                speicherleistung = 0
            try:
                speichersoc = int(SubData.bat_all_data.data.get.soc)
            except Exception:
                log.exception("Fehler beim Auslesen der Ramdisk  (Speichersoc)")
                speichersoc = 0
            watt = SubData.counter_data[f"counter{SubData.counter_all_data.get_id_evu_counter()}"].data.get.power * -1
            wattint = int(watt)
            pvwatt = int(SubData.pv_all_data.data.get.power) * -1
            testwatt = int(SubData.cp_all_data.data.get.power)
            if (testwatt <= 1000):
                chargestatus = False
            else:
                chargestatus = True
            mainloop(wattint, speicherleistung, speichersoc, pvwatt, chargestatus)
        except Exception:
            log.exception("Fehler im Smarthome-Handler")
    # run as thread for logging reasons
    initparam(mqttcg, mqttcs, mqttsdevstat, mqttsglobstat, mqtttopicdisengageable, ramdiskwrite, mqttport)
    for thread in threading.enumerate():
        if thread.name == "smarthome":
            log.debug("Don't start multiple instances of smarthome thread.")
            return
    Thread(target=handler, args=(), name="smarthome").start()
