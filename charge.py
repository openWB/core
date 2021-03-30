""" Starten des Lade-Vorgangs
"""

import requests
import time
from pymodbus.client.sync import ModbusTcpClient

import data
import log
import pub

class charge():
    def __init__(self):
        pass

    def start_charging(self):
        try:
            log.message_debug_log("debug", "# Ladung starten.")
            data.pv_data["pv"].put_stats()
            data.counter_data["evu"].put_stats()
            for cp in data.cp_data:
                if "cp" in cp:
                    chargepoint = data.cp_data[cp]
                    if "set" in chargepoint.data:
                        if "charging_ev" in chargepoint.data["set"]:
                            self._initiate_control_pilot_interruption(chargepoint)
                            self._initiate_phase_switch(chargepoint)
                            self._update_state(chargepoint)
        except Exception as e:
            log.exception_logging(e)

    def _initiate_control_pilot_interruption(self, chargepoint):
        """ prüft, ob eine Control Pilot- Unterbrechung erforderlich ist und führt diese durch.
        """
        try:
            charging_ev = chargepoint.data["set"]["charging_ev"]
            # War die Ladung pausiert?

            # # Ist Control Pilot-Unterbrechung hardwareseitig möglich und ist die Control Pilot-Unterbrechung für das EV erforderlich?
            # if chargepoint.data["config"]["control_pilot_interruption_hw"] == True and charging_ev.ev_template.data["control_pilot_interruption"] == True:
            # # 50s warten bis CP-Skript aufgerufen wird?
            #     log.message_debug_log("debug", "# Control-Pilot-Unterbrechung an LP"+str(chargepoint.cp_num)+" fuer "+charging_ev.ev_template.data["control_pilot_interruption_duration"]+"s durchfuehren.")
            #     # Skript der jeweiligen EVSE-Verbindung aufrufen
            #     if [[ $evsecon == "simpleevsewifi" ]]; then
            #         response = requests.get('http:///$evsewifiiplp1/interruptCp')
            #     elif [[ $evsecon == "ipevse" ]]; then
            #         self._force_control_pilot_interruption_remote()
            #     elif [[ $evsecon == "extopenwb" ]]; then
            #         mosquitto_pub -r -t openWB/set/isss/Cpulp1 -h $chargep1ip -m "1"
            #     else
            #         chargepoint.perform_control_pilot_interruption(charging_ev.ev_template.data["control_pilot_interruption_duration"])
        except Exception as e:
            log.exception_logging(e)

    def _force_control_pilot_interruption_remote(self, ip_address, modbus_id, duration):
        client = ModbusTcpClient(ip_address, port=8899)
        rq = client.write_register(0x0001, 256, unit=modbus_id)
        time.sleep(duration)
        rq = client.write_register(0x0001, 512, unit=modbus_id)

    def _initiate_phase_switch(self, chargepoint):
        """prüft, ob eine Phasenumschaltung erforderlich ist und führt diese durch.
        """
        try:
            if chargepoint.data["get"]["phases_in_use"] != chargepoint.data["set"]["phases_to_use"]:
                #perform hw phase switch
                pub.pub("openWB/chargepoint/"+str(chargepoint.cp_num)+"/set/phases_to_use", chargepoint.data["set"]["phases_to_use"])
                pub.pub("openWB/chargepoint/"+str(chargepoint.cp_num)+"/set/current", chargepoint.data["set"]["charging_ev"].data["control_parameter"]["required_current"])
        except Exception as e:
            log.exception_logging(e)

    def _update_state(self, chargepoint):
        """aktualisiert den Zustand des Ladepunkts.
        """
        try:
            if chargepoint.data["set"]["current"]  != 0:
                chargepoint.hw_data["get"]["charge_state"] == True
            else:
                chargepoint.hw_data["get"]["charge_state"] == False
            pub.pub("openWB/chargepoint/"+str(chargepoint.cp_num)+"/get/charge_state", chargepoint.hw_data["get"]["charge_state"])
            pub.pub("openWB/chargepoint/"+str(chargepoint.cp_num)+"/get/power_all", (chargepoint.data["set"]["phases_to_use"]*chargepoint.data["set"]["current"]*230))
        except Exception as e:
            log.exception_logging(e)
