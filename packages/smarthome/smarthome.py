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
mqttcs = 'openWB/LegacySmartHome/config/set/'
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
                if len(SubData.bat_data) > 1:
                    speicherleistung = int(SubData.bat_all_data.data.get.power)
                    speichersoc = int(SubData.bat_all_data.data.get.soc)
                else:
                    speicherleistung = 0
                    speichersoc = 100
            except Exception:
                log.exception("Fehler beim Auslesen der Ramdisk " +
                              "(speichervorhanden,speicherleistung,speichersoc): ")
                speicherleistung = 0
                speichersoc = 100
            watt = SubData.counter_data[f"counter{SubData.counter_all_data.get_id_evu_counter()}"].data.get.power * -1
            wattint = int(watt)
            mainloop(wattint, speicherleistung, speichersoc)
        except Exception:
            log.exception("Fehler im Smarthome-Handler")
    # run as thread for logging reasons
    initparam(mqttcg, mqttcs, mqttsdevstat, mqttsglobstat, mqtttopicdisengageable, ramdiskwrite, mqttport)
    for thread in threading.enumerate():
        if thread.name == "smarthome":
            log.debug("Don't start multiple instances of smarthome thread.")
            return
    Thread(target=handler, args=(), name="smarthome").start()
