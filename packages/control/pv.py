"""PV-Logik
Die Leistung, die die PV-Module liefern, kann nicht komplett für das Laden und Smarthome verwendet werden.
Davon ab geht z.B. noch der Hausverbrauch. Für das Laden mit PV kann deshalb nur der Strom verwendet werden,
der sonst in das Netz eingespeist werden würde.
"""

import logging
from typing import Tuple

from control import algorithm
from control import data
from control.chargepoint import Chargepoint
from helpermodules.pub import Pub
from helpermodules import timecheck

log = logging.getLogger(__name__)


class PvAll:
    """
    """

    def __init__(self):
        self.data = {
            "set": {"overhang_power_left": 0,
                    "available_power": 0},
            "get": {"power": 0},
            "config": {"configured": False}}
        self.reset_pv_data()

    def calc_power_for_all_components(self) -> None:
        try:
            if len(data.data.pv_data) > 1:
                # Summe von allen konfigurierten Modulen
                self.data["get"]["counter"] = 0
                self.data["get"]["daily_yield"] = 0
                self.data["get"]["monthly_yield"] = 0
                self.data["get"]["yearly_yield"] = 0
                self.data["get"]["power"] = 0
                for module in data.data.pv_data:
                    try:
                        if "pv" in module:
                            self.data["get"]["power"] += data.data.pv_data[module].data["get"]["power"]
                            self.data["get"]["counter"] += data.data.pv_data[module].data["get"]["counter"]
                            self.data["get"]["daily_yield"] += data.data.pv_data[module].data["get"]["daily_yield"]
                            self.data["get"]["monthly_yield"] += data.data.pv_data[module].data["get"]["monthly_yield"]
                            self.data["get"]["yearly_yield"] += data.data.pv_data[module].data["get"]["yearly_yield"]
                    except Exception:
                        log.exception("Fehler im allgemeinen PV-Modul für "+str(module))
                # Alle Summentopics im Dict publishen
                {Pub().pub("openWB/set/pv/get/"+k, v) for (k, v) in self.data["get"].items()}
                self.data["config"]["configured"] = True
                Pub().pub("openWB/set/pv/config/configured", self.data["config"]["configured"])
            else:
                self.data["config"]["configured"] = False
                Pub().pub("openWB/set/pv/config/configured", self.data["config"]["configured"])
                {Pub().pub("openWB/pv/get/"+k, 0) for (k, _) in self.data["get"].items()}
        except Exception:
            log.exception("Fehler im allgemeinen PV-Modul")

    def calc_power_for_control(self):
        """ berechnet den EVU-Überschuss, der in der Regelung genutzt werden kann.
        Regelmodus: Wenn möglichst der ganze PV-Strom genutzt wird, sollte die EVU-Leistung irgendwo
            im Bereich um 0 leigen. Um ein Aufschwingen zu vermeiden, sollte die verfügbare Leistung nur
            angepasst werden, wenn sie außerhalb des Regelbereichs liegt.

        Return
        ------
        int: PV-Leistung, die genutzt werden darf (auf allen Phasen/je Phase unterschiedlich?)
        """
        try:
            if self.data["config"]["configured"] is True:
                # aktuelle Leistung an der EVU, enthält die Leistung der Einspeisegrenze
                evu_overhang = data.data.counter_data[data.data.counter_data["all"].get_evu_counter(
                )].data["get"]["power"]

                # Regelmodus
                control_range_low = data.data.general_data["general"].data[
                    "chargemode_config"]["pv_charging"]["control_range"][0]
                control_range_high = data.data.general_data["general"].data[
                    "chargemode_config"]["pv_charging"]["control_range"][1]
                control_range_center = control_range_high - \
                    (control_range_high - control_range_low) / 2
                if control_range_low < evu_overhang < control_range_high:
                    available_power = 0
                else:
                    available_power = (evu_overhang - control_range_center) * -1

                self.data["set"]["overhang_power_left"] = available_power
                log.debug(
                    str(self.data["set"]["overhang_power_left"]) +
                    "W EVU-Überschuss, der für die Regelung verfügbar ist, davon " +
                    str(self.data["set"]["reserved_evu_overhang"]) +
                    "W für die Einschaltverzögerung reservierte Leistung.")
            # nur allgemeiner PV-Key vorhanden, d.h. kein Modul konfiguriert
            else:
                self.data["config"]["configured"] = False
                available_power = 0
                log.debug("Kein PV-Modul konfiguriert.")
                self.data["set"]["overhang_power_left"] = 0
            self.data["set"]["available_power"] = available_power
            Pub().pub("openWB/set/pv/set/available_power", available_power)
        except Exception:
            log.exception("Fehler im allgemeinen PV-Modul")

    def switch_on(self,
                  chargepoint: Chargepoint,
                  required_current: float,
                  phases: int,
                  bat_overhang: float) -> Tuple[float, bool]:
        """ prüft, ob die Einschaltschwelle erreicht wurde, reserviert Leistung und gibt diese frei
        bzw. stoppt die Freigabe wenn die Ausschaltschwelle und -verzögerung erreicht wurde.

        Erst wenn für eine bestimmte Zeit eine bestimmte Grenze über/unter-
        schritten wurde, wird die Ladung gestartet/gestoppt. So wird häufiges starten/stoppen
        vermieden. Die Grenzen aus den Einstellungen sind als Deltas zu verstehen, die absoluten
        Schaltpunkte ergeben sich ggf noch aus der Einspeisegrenze.
        """
        try:
            required_power = required_current * phases * 230
            threshold_reached = True
            pv_config = data.data.general_data["general"].data["chargemode_config"]["pv_charging"]
            feed_in_limit = chargepoint.data["set"]["charging_ev_data"].charge_template.data["chargemode"][
                "pv_charging"]["feed_in_limit"]
            feed_in_yield = pv_config["feed_in_yield"]
            control_parameter = chargepoint.data["set"]["charging_ev_data"].data["control_parameter"]
            # verbleibender EVU-Überschuss unter Berücksichtigung der Einspeisegrenze
            all_overhang = self.overhang_left()
            # Berücksichtigung der Speicherleistung
            all_overhang += bat_overhang
            if max(chargepoint.data["get"]["currents"]) == 0:
                if control_parameter["timestamp_switch_on_off"] is not None:
                    # Wurde die Einschaltschwelle erreicht? Reservierte Leistung aus all_overhang rausrechnen,
                    # da diese Leistung ja schon reserviert wurde, als die Einschaltschwelle erreicht wurde.
                    if ((not feed_in_limit and
                            all_overhang + required_power > pv_config["switch_on_threshold"]*phases) or
                            (feed_in_limit and
                             all_overhang + required_power >= feed_in_yield)):
                        # Timer ist noch nicht abgelaufen
                        if timecheck.check_timestamp(
                                control_parameter["timestamp_switch_on_off"],
                                pv_config["switch_on_delay"]):
                            required_power = 0
                            chargepoint.data["get"]["state_str"] = "Die Ladung wird gestartet, sobald nach "+str(
                                pv_config["switch_on_delay"]) + "s die Einschaltverzögerung abgelaufen ist."
                        # Timer abgelaufen
                        else:
                            control_parameter["timestamp_switch_on_off"] = None
                            self.data["set"]["reserved_evu_overhang"] -= pv_config["switch_on_threshold"]*phases
                            log.info(
                                "Einschaltschwelle von " + str(pv_config["switch_on_threshold"]) +
                                "W für die Dauer der Einschaltverzögerung überschritten.")
                            Pub().pub(
                                "openWB/set/vehicle/" + str(chargepoint.data["set"]["charging_ev_data"].ev_num) +
                                "/control_parameter/timestamp_switch_on_off", None)
                    # Einschaltschwelle wurde unterschritten, Timer zurücksetzen
                    else:
                        control_parameter["timestamp_switch_on_off"] = None
                        self.data["set"]["reserved_evu_overhang"] -= pv_config["switch_on_threshold"]*phases
                        required_power = 0
                        message = "Einschaltschwelle von " + \
                            str(pv_config["switch_on_threshold"]) + \
                            "W während der Einschaltverzögerung unterschritten."
                        log.info("LP "+str(chargepoint.cp_num)+": "+message)
                        chargepoint.data["get"]["state_str"] = message
                        Pub().pub(
                            "openWB/set/vehicle/" + str(chargepoint.data["set"]["charging_ev_data"].ev_num) +
                            "/control_parameter/timestamp_switch_on_off", None)
                        threshold_reached = False
                else:
                    # Timer starten
                    if ((not feed_in_limit and all_overhang > pv_config["switch_on_threshold"]*phases) or
                            (feed_in_limit and all_overhang >= feed_in_yield and
                             self.data["set"]["reserved_evu_overhang"] == 0)):
                        control_parameter["timestamp_switch_on_off"] = timecheck.create_timestamp(
                        )
                        self.data["set"]["reserved_evu_overhang"] += pv_config["switch_on_threshold"]*phases
                        required_power = 0
                        message = "Die Ladung wird gestartet, sobald nach " + \
                            str(pv_config["switch_on_delay"]) + \
                            "s die Einschaltverzögerung abgelaufen ist."
                        log.info("LP "+str(chargepoint.cp_num)+": "+message)
                        chargepoint.data["get"]["state_str"] = message
                        Pub().pub(
                            "openWB/set/vehicle/" + str(chargepoint.data["set"]["charging_ev_data"].ev_num) +
                            "/control_parameter/timestamp_switch_on_off", control_parameter
                            ["timestamp_switch_on_off"])
                    else:
                        # Einschaltschwelle nicht erreicht
                        message = "Die Ladung kann nicht gestartet werden, da die Einschaltschwelle ("+str(
                            pv_config["switch_on_threshold"])+"W) nicht erreicht wird."
                        log.info("LP "+str(chargepoint.cp_num)+": "+message)
                        if chargepoint.data["get"]["state_str"] is None:
                            chargepoint.data["get"]["state_str"] = message
                        required_power = 0
                        threshold_reached = False
            else:
                chargepoint.data["get"]["state_str"] = "Die Ladung wurde aufgrund des EV-Profils ohne \
                    Einschaltverzögerung gestartet, um die Ladung nicht zu unterbrechen."

            if required_power != 0:
                allocated_current, _ = algorithm.allocate_power(
                    chargepoint, required_current, phases)
            else:
                allocated_current = 0
            return allocated_current, threshold_reached
        except Exception:
            log.exception("Fehler im allgemeinen PV-Modul")
            return 0, False

    def switch_off_check_timer(self, chargepoint):
        """ prüft, ob der Timer der Ausschaltverzögerung abgelaufen ist.

        Parameter
        ---------
        chargepoint: dict
            Daten des Ladepunkts

        Return
        ------
        True: Timer abgelaufen
        False: Timer noch nicht abgelaufen
        """
        try:
            pv_config = data.data.general_data["general"].data["chargemode_config"]["pv_charging"]
            control_parameter = chargepoint.data["set"]["charging_ev_data"].data["control_parameter"]

            if control_parameter["timestamp_switch_on_off"] is not None:
                if not timecheck.check_timestamp(
                        control_parameter["timestamp_switch_on_off"],
                        pv_config["switch_off_delay"]):
                    control_parameter["timestamp_switch_on_off"] = None
                    self.data["set"]["released_evu_overhang"] -= chargepoint.data["set"]["required_power"]
                    message = "Ladevorgang nach Ablauf der Abschaltverzögerung gestoppt."
                    log.info("LP "+str(chargepoint.cp_num)+": "+message)
                    chargepoint.data["get"]["state_str"] = message
                    Pub().pub(
                        "openWB/set/vehicle/" + str(chargepoint.data["set"]["charging_ev_data"].ev_num) +
                        "/control_parameter/timestamp_switch_on_off", None)
                    return True
                else:
                    chargepoint.data["get"]["state_str"] = "Ladevorgang wird nach Ablauf der Abschaltverzögerung (" + \
                        str(pv_config["switch_off_delay"])+"s) gestoppt."
            return False
        except Exception:
            log.exception("Fehler im allgemeinen PV-Modul")
            return False

    def switch_off_check_threshold(self, chargepoint: Chargepoint, overhang: float) -> None:
        """ prüft, ob die Abschaltschwelle erreicht wurde und startet die Abschaltverzögerung.
        Ist die Abschaltverzögerung bereits aktiv, wird geprüft, ob die Abschaltschwelle wieder
        unterschritten wurde, sodass die Verzögerung wieder gestoppt wird.
        """
        try:
            control_parameter = chargepoint.data["set"]["charging_ev_data"].data["control_parameter"]
            pv_config = data.data.general_data["general"].data["chargemode_config"]["pv_charging"]
            # Der EVU-Überschuss muss ggf um die Einspeisegrenze bereinigt werden.
            if chargepoint.data["set"]["charging_ev_data"].charge_template.data["chargemode"]["pv_charging"][
                    "feed_in_limit"]:
                feed_in_yield = data.data.general_data["general"].data[
                    "chargemode_config"]["pv_charging"]["feed_in_yield"]
            else:
                feed_in_yield = 0
            log.debug(f'LP{chargepoint.cp_num} Switch-Off-Threshold prüfen: EVU {overhang}W, freigegebener '
                      f'Überschuss {self.data["set"]["released_evu_overhang"]}W, Einspeisungsgrenze {feed_in_yield}W')
            # Wenn automatische Phasenumschaltung aktiv, erstmal die Umschaltung abwarten, bevor die Abschaltschwelle
            # greift.
            if control_parameter["timestamp_auto_phase_switch"] is None:
                if control_parameter["timestamp_switch_on_off"]:
                    # Wurde die Abschaltschwelle erreicht?
                    # Eigene Leistung aus der freigegebenen Leistung rausrechnen.
                    if ((overhang +
                            self.data["set"]["released_evu_overhang"] -
                            chargepoint.data["set"]["required_power"])
                            < (pv_config["switch_off_threshold"] + feed_in_yield)):
                        control_parameter["timestamp_switch_on_off"] = None
                        self.data["set"]["released_evu_overhang"] -= chargepoint.data["set"]["required_power"]
                        log.info("Abschaltschwelle während der Verzögerung überschritten.")
                        Pub().pub(
                            "openWB/set/vehicle/" + str(chargepoint.data["set"]["charging_ev_data"].ev_num) +
                            "/control_parameter/timestamp_switch_on_off", None)
                else:
                    # Wurde die Abschaltschwelle ggf. durch die Verzögerung anderer LP erreicht?
                    if ((overhang + self.data["set"]["released_evu_overhang"]) >
                            (pv_config["switch_off_threshold"] + feed_in_yield)):
                        if not chargepoint.data["set"]["charging_ev_data"].ev_template.data["prevent_charge_stop"]:
                            control_parameter["timestamp_switch_on_off"] = timecheck.create_timestamp()
                            # merken, dass ein LP verzögert wird, damit nicht zu viele LP verzögert werden.
                            self.data["set"]["released_evu_overhang"] += chargepoint.data["set"]["required_power"]
                            message = "Ladevorgang wird nach Ablauf der Abschaltverzögerung (" + str(
                                pv_config["switch_off_delay"])+"s) gestoppt."
                            log.info("LP "+str(chargepoint.cp_num)+": "+message)
                            chargepoint.data["get"]["state_str"] = message
                            Pub().pub(
                                "openWB/set/vehicle/" + str(chargepoint.data["set"]["charging_ev_data"].ev_num) +
                                "/control_parameter/timestamp_switch_on_off", control_parameter
                                ["timestamp_switch_on_off"])
                            # Die Abschaltschwelle wird immer noch überschritten und es sollten weitere LP abgeschaltet
                            # werden.
                        else:
                            msg = "Stoppen des Ladevorgangs aufgrund des EV-Profils verhindert."
                            chargepoint.data["get"]["state_str"] = msg
                            log.info(f"LP {chargepoint.cp_num}: {msg}")
        except Exception:
            log.exception("Fehler im allgemeinen PV-Modul")

    def reset_switch_on_off(self, chargepoint, charging_ev):
        """ Zeitstempel und reservierte Leistung löschen

        Parameter
        ---------
        chargepoint: dict
            Ladepunkt, für den die Werte zurückgesetzt werden sollen
        charging_ev: dict
            EV, das dem Ladepunkt zugeordnet ist
        """
        try:
            if charging_ev.data["control_parameter"]["timestamp_switch_on_off"] is not None:
                charging_ev.data["control_parameter"]["timestamp_switch_on_off"] = None
                Pub().pub("openWB/set/vehicle/"+str(charging_ev.ev_num) +
                          "/control_parameter/timestamp_switch_on_off", None)
                # Wenn bereits geladen wird, freigegebene Leistung freigeben. Wenn nicht geladen wird, reservierte
                # Leistung freigeben.
                pv_config = data.data.general_data["general"].data["chargemode_config"]["pv_charging"]
                if not chargepoint.data["get"]["charge_state"]:
                    data.data.pv_data["all"].data["set"]["reserved_evu_overhang"] -= pv_config[
                        "switch_on_threshold"] * chargepoint.data["set"]["phases_to_use"]
                    log.debug("reserved_evu_overhang 10 " +
                              str(data.data.pv_data["all"].data["set"]["reserved_evu_overhang"]))
                else:
                    data.data.pv_data["all"].data["set"]["released_evu_overhang"] -= pv_config[
                        "switch_on_threshold"] * charging_ev.data["control_parameter"]["phases"]
                    log.debug("reserved_evu_overhang 11 " +
                              str(data.data.pv_data["all"].data["set"]["reserved_evu_overhang"]))
        except Exception:
            log.exception("Fehler im allgemeinen PV-Modul")

    def overhang_left(self):
        """ gibt den verfügbaren EVU-Überschuss zurück.

        Return
        ------
        overhang_power_left: int
            verfügbarer EVU-Überschuss + bereits genutzter Überschuss
        """
        try:
            if self.data["config"]["configured"]:
                return self.data["set"]["overhang_power_left"] - self.data["set"]["reserved_evu_overhang"]
            else:
                return 0
        # return available pv power with feed in yield
        except Exception:
            log.exception("Fehler im allgemeinen PV-Modul")
            return 0

    def allocate_evu_power(self, required_power):
        """ subtrahieren der zugeteilten Leistung vom verfügbaren EVU-Überschuss

        Parameter
        ---------
        required_power: float
            Leistung, mit der geladen werden soll

        Return
        ------
        True: Leistung konnte zugeteilt werden.
        False: Leistung konnte nicht zugeteilt werden.
        """
        try:
            if self.data["config"]["configured"]:
                self.data["set"]["overhang_power_left"] -= required_power
                log.debug(
                    str(self.data["set"]["overhang_power_left"]) +
                    "W EVU-Überschuss, der für die folgenden Ladepunkte übrig ist, davon " +
                    str(self.data["set"]["reserved_evu_overhang"]) +
                    "W für die Einschaltverzögerung reservierte Leistung.")
                # Float-Ungenauigkeiten abfangen
                if self.data["set"]["overhang_power_left"] < -0.01:
                    # Fehlermeldung nur ausgeben, wenn Leistung zugeteilt wird.
                    # Es kann nicht immer mit einem LP so viel Leistung freigegeben werden, dass die verfügbare
                    # Leistung positiv ist.
                    if required_power > 0:
                        log.error(
                            "Es wurde versucht, mehr EVU-Überschuss zuzuteilen, als vorhanden ist.")
                    too_much = self.data["set"]["overhang_power_left"]
                    self.data["set"]["overhang_power_left"] = 0
                    return too_much
            return 0
        except Exception:
            log.exception("Fehler im allgemeinen PV-Modul")
            return required_power

    def put_stats(self):
        """ Publishen und Loggen des verbleibenden EVU-Überschusses und reservierten Leistung
        """
        try:
            Pub().pub("openWB/set/pv/config/configured",
                      self.data["config"]["configured"])
            if self.data["config"]["configured"]:
                Pub().pub("openWB/set/pv/set/overhang_power_left",
                          self.data["set"]["overhang_power_left"])
                Pub().pub("openWB/set/pv/set/reserved_evu_overhang",
                          self.data["set"]["reserved_evu_overhang"])
                Pub().pub("openWB/set/pv/set/released_evu_overhang",
                          self.data["set"]["released_evu_overhang"])
        except Exception:
            log.exception("Fehler im allgemeinen PV-Modul")

    def reset_pv_data(self):
        """ setzt die Daten zurück, die über mehrere Regelzyklen genutzt werden.
        """
        try:
            Pub().pub("openWB/set/pv/set/reserved_evu_overhang", 0)
            Pub().pub("openWB/set/pv/set/released_evu_overhang", 0)
            self.data["set"]["reserved_evu_overhang"] = 0
            self.data["set"]["released_evu_overhang"] = 0
        except Exception:
            log.exception("Fehler im allgemeinen PV-Modul")

    def print_stats(self):
        try:
            log.debug(
                str(self.data["set"]["overhang_power_left"]) +
                "W EVU-Überschuss, der für die Regelung verfügbar ist, davon " +
                str(self.data["set"]["reserved_evu_overhang"]) +
                "W für die Einschaltverzögerung reservierte Leistung.")
        except Exception:
            log.exception("Fehler im allgemeinen PV-Modul")


def get_inverter_default_config():
    return {"max_ac_out": 0}


class Pv:

    def __init__(self, index):
        self.data = {
            "get": {
                "daily_yield": 0,
                "monthly_yield": 0,
                "yearly_yield": 0
            },
            "config": {}
        }
        self.pv_num = index
