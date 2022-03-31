""" Algorithmus zur Berechnung der Ladeströme
"""

import copy
import logging
from typing import Dict, List, Optional, Tuple

from control import data
from control import loadmanagement
from control.chargepoint import Chargepoint
from helpermodules.pub import Pub

log = logging.getLogger(__name__)


class Algorithm:
    """Verteilung des Stroms auf die Ladepunkte
    """

    def __init__(self):
        # Lademodi in absteigender Priorität; Tupel-Inhalt:(eingestellter Modus, tatsächlich genutzter Modus, Priorität)
        self.chargemodes = (("scheduled_charging", "instant_charging", True),
                            ("scheduled_charging", "instant_charging", False),
                            (None, "time_charging", True),
                            (None, "time_charging", False),
                            ("instant_charging", "instant_charging", True),
                            ("instant_charging", "instant_charging", False),
                            ("pv_charging", "instant_charging", True),
                            ("pv_charging", "instant_charging", False),
                            ("scheduled_charging", "pv_charging", True),
                            ("scheduled_charging", "pv_charging", False),
                            ("pv_charging", "pv_charging", True),
                            ("pv_charging", "pv_charging", False),
                            (None, "standby", True),
                            (None, "standby", False),
                            (None, "stop", True),
                            (None, "stop", False))

    def calc_current(self) -> None:
        """ Einstiegspunkt in den Regel-Algorithmus
        """
        try:
            log.debug("# Algorithmus-Start")
            evu_counter = data.data.counter_data["all"].get_evu_counter()
            log.info(
                f'EVU-Punkt: Leistung[W] {data.data.counter_data[evu_counter].data["get"]["power"]}, Ströme[A] '
                f'{data.data.counter_data[evu_counter].data["get"].get("currents")}')

            # zuerst die PV-Überschuss-Ladung zurück nehmen
            self._reduce_used_evu_overhang()

            # Lastmanagement für alle Zähler
            self._check_loadmanagement()

            # Abschaltschwelle prüfen und ggf. Abschaltverzögerung starten
            for mode in reversed(self.chargemodes[8:-4]):
                self._switch_off_threshold(mode)

            # Phasenumschaltung
            self._check_auto_phase_switch_delay()

            # Überschuss auf Ladepunkte verteilen
            self._manage_distribution()

            # Übrigen Überschuss auf Ladepunkte im PV-Modus verteilen
            self._distribute_unused_evu_overhang()

            # LP stoppen, bei denen die Abschaltverzögerung abgelaufen ist (die frei werdende Leistung soll erst
            # im nächsten Zyklus verteilt werden)
            self._stop_after_switch_off_delay()
        except Exception:
            log.exception("Fehler im Algorithmus-Modul")

    def _reduce_used_evu_overhang(self) -> None:
        """ nimmt den Ladestrom, der über der eingestellten Stromstärke liegt, zurück, um zu schauen, ob er im
        Algorithmus anderweitig verteilt wird.
        Wenn nein, wird er am Ende wieder zugeteilt.

        Alle EV im PV-Modus sollen laden, bevor eine Phasenumschaltung stattfindet. Deshalb wird zu Beginn des
        Algorithmus der übrige Überschuss zurückgenommen und steht dann im weiteren Algorithmus, z.B. zum Erreichen
        der Einschaltschwelle für ein weiteres EV, zur Verfügung.
        """
        log.info("## Überschuss-Ladung über Mindeststrom bei PV-Laden zurücknehmen.")
        for cp in data.data.cp_data.values():
            if isinstance(cp, Chargepoint):
                try:
                    if "current" in cp.data["set"]:
                        if cp.data["set"]["current"] == 0:
                            continue
                        if cp.data["set"]["charging_ev"] != -1:
                            charging_ev = cp.data["set"]["charging_ev_data"]
                            # Wenn beim PV-Laden über der eingestellten Stromstärke geladen wird, zuerst zurücknehmen.
                            if((charging_ev.charge_template.data["chargemode"]["selected"] == "pv_charging" or
                                    charging_ev.data["control_parameter"]["submode"] == "pv_charging") and
                                    cp.data["set"]["current"] != 0):
                                if max(cp.data["get"]["currents"]) != 0:
                                    # Strom, mit dem tatsächlich geladen wird, verwenden, da man sonst mehr Strom
                                    # freigibt, als zur Verfügung steht.
                                    released_current = charging_ev.data["control_parameter"]["required_current"] - max(
                                        cp.data["get"]["currents"])
                                    released_power = released_current * 230 * cp.data["get"]["phases_in_use"]
                                    # Nur wenn mit mehr als der benötigten Stromstärke geladen wird, kann der
                                    # Überschuss ggf anderweitig in der Regelung verwendet werden.
                                    if released_current < 0:
                                        data.data.pv_data["all"].allocate_evu_power(released_power)
                                        self._process_data(
                                            cp, charging_ev.data["control_parameter"]["required_current"])
                                        loadmanagement.loadmanagement_for_cp(
                                            cp,
                                            released_current,
                                            cp.data["get"]["phases_in_use"])
                                        log.debug(
                                            "Ladung an LP" + str(cp.cp_num) + " um " + str(released_current) +
                                            "A auf " + str(charging_ev.data["control_parameter"]["required_current"]) +
                                            "A angepasst.")
                                else:
                                    # Wenn das EV nicht laden will, trotztdem zugeteilten Überschuss zurücknehmen,
                                    # da es sonst ggf mit einer zu hohen Soll-Stromstärke anfängt zu laden, wenn es
                                    # dann doch noch anfängt. Dieser Strom darf aber nicht freigegeben werden, da er
                                    # keine Auswirkungen auf den EVU-Überschuss hat.
                                    self._process_data(
                                        cp, charging_ev.data["control_parameter"]["required_current"])
                                    log.debug(
                                        "Ladung an LP" + str(cp.cp_num) + " auf " +
                                        str(charging_ev.data["control_parameter"]["required_current"]) +
                                        "A angepasst.")
                except Exception:
                    log.exception(f"Fehler im Algorithmus-Modul für Ladepunkt {cp.cp_num}")

    def _check_loadmanagement(self) -> None:
        """ prüft, ob an einem der Zähler das Lastmanagement aktiv ist.
        """
        try:
            loadmanagement_state, overloaded_counters = loadmanagement.loadmanagement_for_counters()
            if loadmanagement_state:
                log.warning("## Ladung wegen aktiven Lastmanagements stoppen.")
                # Zähler mit der größten Überlastung ermitteln
                overloaded_counters = sorted(
                    overloaded_counters.items(), key=lambda e: e[1][1], reverse=True)
                n = 0  # Zähler, der betrachtet werden soll
                # set current auf den maximalen get current stellen, damit der tatsächlich genutzte Strom reduziert
                # wird und nicht der maximal nutzbare, der ja eventuell gar nicht voll ausgenutzt wird, sodass die
                # Reduzierung wirkungslos wäre. Wenn set current bereits reduziert wurde, darf es nicht wieder
                # hochgesetzt werden. EVs, die nicht laden, sollen nicht berücksichtigt werden.
                for cp in data.data.cp_data.values():
                    if isinstance(cp, Chargepoint):
                        try:
                            max_get_current = max(cp.data["get"]["currents"])
                            if (cp.data["set"]["current"] > max_get_current
                                > cp.data["set"][
                                    "charging_ev_data"].ev_template.data["nominal_difference"]):
                                # Manche EVs laden mit weniger Strom als der Min-Strom.
                                if (max_get_current > cp.data["set"][
                                        "charging_ev_data"].ev_template.data["min_current"]):
                                    cp.data["set"]["current"] = max_get_current
                                else:
                                    cp.data["set"]["current"] = cp.data["set"][
                                        "charging_ev_data"].ev_template.data["min_current"]
                        except Exception:
                            log.exception(f"Fehler im Algorithmus-Modul für Ladepunkt {cp.cp_num}")
                # Begrenzung der Schleifendurchläufe: Im ersten Durchlauf wird versucht, die Überlast durch Reduktion
                # zu eliminieren, im zweiten durch Abschalten. Daher die zweifache Anzahl von Zählern als Durchläufe.
                for b in range(0, len(data.data.counter_data)*2):
                    chargepoints = data.data.counter_data["all"].get_chargepoints_of_counter(
                        overloaded_counters[n][0])
                    overshoot = overloaded_counters[n][1][0]
                    # Das Lademodi-Tupel rückwärts durchgehen und LP mit niedrig priorisiertem Lademodus zuerst
                    # reduzieren/stoppen.
                    for mode in reversed(self.chargemodes[:-4]):
                        overshoot = self._down_regulation(
                            mode, chargepoints, overshoot, overloaded_counters[n][1][1])
                        if overshoot == 0:
                            break
                    # Wenn kein Ladepunkt lädt, kann die Wallbox nichts am Lastmanagement ausrichten. Die Überlastung
                    # kommt ausschließlich vom Hausverbrauch.
                    for cp in data.data.cp_data.values():
                        if isinstance(cp, Chargepoint):
                            try:
                                if cp.data["set"]["current"] != 0:
                                    break
                            except Exception:
                                log.exception(f"Fehler im Algorithmus-Modul für Ladepunkt {cp.cp_num}")
                    else:
                        log.warning("Überlastung wird durch Hausverbrauch verursacht.")
                        break
                    if overshoot == 0:
                        # Nach dem Aktualisieren der Werte sollte der Zähler verschwunden sein, weil man genügend LP
                        # abschalten konnte
                        n = 0
                    else:
                        # Wenn die Überlastung nicht komplett beseitigt werden konnte, Zahlen aktualisieren und mit
                        # nächstem Zähler weitermachen.
                        n += 1
                    if n > len(overloaded_counters)-1:
                        # keine Zähler mehr, an denen noch reduziert werden kann. Wieder beim ersten Zähler anfangen,
                        # diesemal werden die
                        # LP dann abgeschaltet.
                        n = 0
                    # Werte aktualisieren
                    loadmanagement_state, overloaded_counters = loadmanagement.loadmanagement_for_counters()
                    if not loadmanagement_state:
                        # Lastmanagement ist nicht mehr aktiv
                        break
                    overloaded_counters = sorted(
                        overloaded_counters.items(), key=lambda e: e[1][1], reverse=True)
            else:
                log.debug(
                    "## Ladung muss nicht wegen aktiven Lastmanagements gestoppt werden.")
            # Ladepunkte, die nicht mit Maximalstromstärke laden, können wieder hochgeregelt werden.
            for mode in self.chargemodes[:-4]:
                self._adjust_chargepoints(mode)
        except Exception:
            log.exception("Fehler im Algorithmus-Modul")

    def _down_regulation(self,
                         mode_tuple: Tuple[Optional[str], str, bool],
                         cps_to_reduce: List[str],
                         max_current_overshoot: float,
                         max_overshoot_phase: int,
                         prevent_stop: bool = False) -> float:
        """ ermittelt die Ladepunkte und in welcher Reihenfolge sie reduziert/abgeschaltet werden sollen und ruft dann
        die Funktion zum Runterregeln auf.
        """
        mode = mode_tuple[0]
        submode = mode_tuple[1]
        prio = mode_tuple[2]
        # LP, die abgeschaltet werden sollen
        preferenced_chargepoints = []
        # enthält alle LP, auf die das Tupel zutrifft
        valid_chargepoints = {}
        for cp in cps_to_reduce:
            try:
                chargepoint = data.data.cp_data[cp]
                if "current" in chargepoint.data["set"]:
                    if chargepoint.data["set"]["current"] == 0:
                        continue
                    if chargepoint.data["set"]["charging_ev"] != -1:
                        charging_ev = chargepoint.data["set"]["charging_ev_data"]
                        # Wenn der LP erst in diesem Zyklus eingeschaltet wird, sind noch keine phases_in_use
                        # hinterlegt.
                        if not chargepoint.data["get"]["charge_state"]:
                            phases = charging_ev.data["control_parameter"]["phases"]
                        else:
                            phases = chargepoint.data["get"]["phases_in_use"]
                        if((charging_ev.charge_template.data["prio"] == prio) and
                                (charging_ev.charge_template.data["chargemode"]["selected"] == mode or
                                    mode is None) and
                                (charging_ev.data["control_parameter"]["submode"] == submode) and
                                # LP muss auf der Phase laden, die überlastet ist.
                                (phases == 3 or max_overshoot_phase == chargepoint.data["config"]["phase_1"] or
                                    chargepoint.data["config"]["phase_1"] == 0)):
                            valid_chargepoints[chargepoint] = None
            except Exception:
                log.exception(f"Fehler im Algorithmus-Modul für Ladepunkt{cp}")
        preferenced_chargepoints = self._get_preferenced_chargepoint(
            valid_chargepoints, False)
        if len(preferenced_chargepoints) != 0:
            log.debug("Zu reduzierende Ladepunkte "+str([cp.cp_num for cp in preferenced_chargepoints]) +
                      " in Lademodus "+str(mode)+" Submodus "+str(submode)+" Prio "+str(prio))
        return self._perform_down_regulation(
            preferenced_chargepoints, max_current_overshoot, max_overshoot_phase, prevent_stop)

    def _perform_down_regulation(
            self,
            preferenced_chargepoints: List[Chargepoint],
            max_current_overshoot: float,
            max_overshoot_phase: int,
            prevent_stop: bool = False) -> float:
        """ prüft, ob der Ladepunkt reduziert werden kann. Wenn Nein und das Abschalten nicht verboten ist, wird der
        Ladepunkt abgeschaltet. Ist noch nicht die Minimalstromstärke erreicht, wird der Ladestrom reduziert.

        max_overshoot_phase: Phase, in der die maximale Stromstärke erreicht wird
                             (0, wenn alle Phasen berücksichtigt werden sollen.)
        """
        message = None
        remaining_current_overshoot = 0
        try:
            if len(preferenced_chargepoints) == 0:
                # Es gibt keine Ladepunkte in diesem Lademodus, die noch nicht laden oder die noch gestoppt werden
                # können.
                return max_current_overshoot
            else:
                for cp in preferenced_chargepoints:
                    try:
                        # Wenn der LP erst in diesem Zyklus eingeschaltet wird, sind noch keine phases_in_use
                        # hinterlegt.
                        ev_data = cp.data["set"]["charging_ev_data"]
                        if not cp.data["get"]["charge_state"]:
                            phases = ev_data.data["control_parameter"]["phases"]
                        else:
                            phases = cp.data["get"]["phases_in_use"]
                        # Wenn max_overshoot_phase -1 ist, wurde die maximale Gesamtleistung überschritten und
                        # max_current_overshoot muss, wenn weniger als 3 Phasen genutzt werden, entsprechend
                        # multipliziert werden.
                        if max_overshoot_phase == -1 and phases < 3:
                            remaining_current_overshoot = max_current_overshoot * \
                                (3 - phases + 1)
                        else:
                            remaining_current_overshoot = max_current_overshoot
                        if cp.data["set"]["current"] != 0:
                            considered_current = cp.data["set"]["current"]
                        else:
                            # Dies ist der aktuell betrachtete Ladepunkt. Es wurde noch kein Strom gesetzt.
                            considered_current = ev_data.data["control_parameter"][
                                "required_current"]
                        adaptable_current = considered_current - \
                            ev_data.ev_template.data["min_current"]
                        # Der Strom kann nicht weiter reduziert werden.
                        if adaptable_current <= 0:
                            # Ladung darf gestoppt werden.
                            if not prevent_stop:
                                taken_current = cp.data["set"]["current"]*-1
                                remaining_current_overshoot += taken_current
                                # In diesem Zyklus darf nicht mehr geladen werden.
                                ev_data.data["control_parameter"]["required_current"] = 0
                                self._process_data(cp, 0)
                                message = "Das Lastmanagement hat den Ladevorgang gestoppt."
                            else:
                                continue
                        else:
                            if adaptable_current < remaining_current_overshoot:
                                remaining_current_overshoot -= adaptable_current
                                taken_current = adaptable_current * -1
                            else:
                                taken_current = remaining_current_overshoot * -1
                                remaining_current_overshoot = 0
                            required_current = considered_current+taken_current
                            self._process_data(cp, required_current)
                            log.debug("LP "+str(cp.cp_num)+": Das Lastmanagement hat den Ladestrom um " +
                                      str(round(taken_current, 2))+"A auf " +
                                      str(round(required_current, 2))+"A angepasst.")
                            current_diff = round(
                                ev_data.data["control_parameter"]["required_current"] - required_current,
                                2)
                            message = f"Das Lastmanagement hat die Sollstromstärke um {current_diff}A runtergeregelt."
                        # Werte aktualisieren
                        loadmanagement.loadmanagement_for_cp(cp, taken_current, phases)
                        data.data.counter_data[data.data.counter_data["all"].get_evu_counter(
                        )].print_stats()
                        # Wenn max_overshoot_phase -1 ist, wurde die maximale Gesamtleistung überschritten und
                        # max_current_overshoot muss, wenn weniger als 3 Phasen genutzt werden, entsprechend dividiert
                        # werden.
                        if max_overshoot_phase == -1 and phases < 3:
                            remaining_current_overshoot = remaining_current_overshoot / \
                                (3 - phases + 1)
                        if remaining_current_overshoot < 0.01:
                            if message is not None:
                                cp.data["get"]["state_str"] = message
                            break
                        else:
                            max_current_overshoot = remaining_current_overshoot
                        if message is not None:
                            cp.data["get"]["state_str"] = message
                    except Exception:
                        log.exception(f"Fehler im Algorithmus-Modul für Ladepunkt {cp.cp_num}")
                return remaining_current_overshoot
        except Exception:
            log.exception("Fehler im Algorithmus-Modul")
            return 0

    def _adjust_chargepoints(self, mode_tuple: Tuple[Optional[str], str, bool]) -> None:
        """ ermittelt die Ladepunkte, die nicht mit der benötigten Stromstärke laden und prüft, ob diese hochgeregelt
        werden können und regelt diese, falls möglich, hoch.
        """
        mode = mode_tuple[0]
        submode = mode_tuple[1]
        prio = mode_tuple[2]
        message = None
        try:
            # LP, der abgeschaltet werden soll
            preferenced_chargepoints = []
            # enthält alle LP, auf die das Tupel zutrifft
            valid_chargepoints = {}
            for cp in data.data.cp_data.values():
                if isinstance(cp, Chargepoint):
                    try:
                        if "current" in cp.data["set"]:
                            if cp.data["set"]["current"] == 0:
                                continue
                            if cp.data["set"]["charging_ev"] != -1:
                                charging_ev = cp.data["set"]["charging_ev_data"]
                                if((charging_ev.charge_template.data["prio"] == prio) and
                                   (charging_ev.charge_template.data["chargemode"]["selected"] == mode or
                                    mode is None) and
                                        (charging_ev.data["control_parameter"]["submode"] == submode) and
                                        (cp.data["set"]["charging_ev_data"].data["control_parameter"][
                                            "required_current"] > cp.data["set"]["current"]) and
                                        # nur die hochregeln, die auch mit der Sollstromstärke laden
                                        (max(cp.data["get"]["currents"]) > cp.data["set"]["current"]
                                         - charging_ev.ev_template.data["nominal_difference"])):
                                    valid_chargepoints[cp] = None
                    except Exception:
                        log.exception("Fehler im Algorithmus-Modul für Ladepunkt"+cp.cp_num)
            preferenced_chargepoints = self._get_preferenced_chargepoint(
                valid_chargepoints, False)

            if len(preferenced_chargepoints) != 0:
                log.info(
                    "## Ladepunkte, die nicht mit Maximalstromstärke laden, wieder hochregeln.")
                log.debug("Hochzuregelnde Ladepunkte "+str([cp.cp_num for cp in preferenced_chargepoints]) +
                          " in Lademodus "+str(mode)+" Submodus "+str(submode)+" Prio "+str(prio))
                for cp in preferenced_chargepoints:
                    try:
                        # aktuelle Werte speichern (werden wieder hergestellt, wenn das Lastmanagement die Anpassung
                        # verhindert)
                        counter_data_old = copy.deepcopy(
                            data.data.counter_data)
                        pv_data_old = copy.deepcopy(data.data.pv_data)
                        bat_data = copy.deepcopy(data.data.bat_data)
                        cp_data_old = copy.deepcopy(data.data.cp_data)
                        # Fehlenden Ladestrom ermitteln
                        missing_current = cp.data["set"]["charging_ev_data"].data[
                            "control_parameter"]["required_current"] - cp.data["set"]["current"]
                        # Wenn der LP erst in diesem Zyklus eingeschaltet wird, sind noch keine phases_in_use
                        # hinterlegt.
                        if cp.data["get"]["phases_in_use"] == 0:
                            phases = cp.data["set"]["charging_ev_data"].data["control_parameter"]["phases"]
                        else:
                            phases = cp.data["get"]["phases_in_use"]
                        # Lastmanagement für den fehlenden Ladestrom durchführen
                        log.debug(
                            (f"LP {cp.cp_num}: Fehlenden Ladestrom anpassen: {missing_current}"))
                        loadmanagement_state, overloaded_counters = loadmanagement.loadmanagement_for_cp(
                            cp, missing_current, phases)
                        log.debug("Lastmanagement aktiv: "+str(loadmanagement_state))
                        if loadmanagement_state:
                            overloaded_counters = sorted(
                                overloaded_counters.items(), key=lambda e: e[1][1], reverse=True)
                            # Wenn max_overshoot_phase -1 ist, wurde die maximale Gesamtleistung überschritten und
                            # max_current_overshoot muss,
                            # wenn weniger als 3 Phasen genutzt werden, entsprechend multipliziert werden.
                            if overloaded_counters[0][1][1] == -1 and phases < 3:
                                undo_missing_current = (
                                    overloaded_counters[0][1][0] * (3 - phases + 1)) * -1
                            else:
                                undo_missing_current = overloaded_counters[0][1][0] * -1
                            # Dies tritt nur ein, wenn Bezug möglich ist, dieser aber unter dem Offset liegt. Dann
                            # wird nämlich durch das Lastmanagement versucht, das Offset auszugleichen.
                            # In diesem Fall soll keine Anpassung erfolgen.
                            if undo_missing_current*-1 > missing_current:
                                # Zustand von vor dem Lastmanagement wieder herstellen
                                data.data.counter_data = counter_data_old
                                data.data.pv_data = pv_data_old
                                data.data.bat_data = bat_data
                                data.data.cp_data = cp_data_old
                                log.debug("Keine Hochregelung für Ladepunkt "+str(cp.cp_num) +
                                          ", da nur noch das Offset zum Maximalstrom verfügbar ist.")
                                message = "Das Lastmanagement konnte den Ladepunkt nicht auf die gewünschte \
                                    Stromstärke hochregeln."
                                # Beim Wiederherstellen der Kopie wird die Adresse der Kopie zugewiesen, sodass die
                                # Adresse des LP aktualisiert werden muss,
                                # um Änderungen in der Klasse vorzunehmen, die das data-Modul referenziert.
                                cp = data.data.cp_data["cp" + str(cp.cp_num)]
                            # Es kann nur ein Teil des fehlenden Ladestroms hochgeregelt werden.
                            else:
                                # Werte aktualisieren
                                loadmanagement.loadmanagement_for_cp(
                                    cp, undo_missing_current, phases)
                                self._process_data(
                                    cp, cp.data["set"]["current"] + missing_current + undo_missing_current)
                                message = "Das Lastmanagement hat den Ladestrom um " + \
                                    str(round(
                                        (missing_current + undo_missing_current), 2))+"A angepasst."
                                log.debug(message)
                        # Zuvor fehlender Ladestrom kann nun genutzt werden
                        else:
                            self._process_data(
                                cp, cp.data["set"]["current"] + missing_current)
                            message = "Das Lastmanagement hat den Ladestrom um " + \
                                str(round(missing_current, 2))+"A angepasst."
                            log.debug(message)
                        ev_data = cp.data["set"]["charging_ev_data"]
                        current_diff = round(ev_data.data[
                            "control_parameter"]["required_current"] - cp.data["set"]["current"], 2)
                        if current_diff > ev_data.ev_template.data["nominal_difference"]:
                            cp.data["get"]["state_str"] = (f"Das Lastmanagement hat die Sollstromstärke um "
                                                           f"{current_diff}A runtergeregelt.")
                    except Exception:
                        log.exception(f"Fehler im Algorithmus-Modul für Ladepunkt {cp.cp_num}")
                data.data.counter_data[data.data.counter_data["all"].get_evu_counter(
                )].print_stats()
        except Exception:
            log.exception("Fehler im Algorithmus-Modul")

    def _switch_off_threshold(self, mode_tuple: Tuple[Optional[str], str, bool]) -> None:
        """Gibt es mehrere Ladepunkte, auf die das Tupel zutrifft, wird die Reihenfolge durch
        _get_preferenced_chargepoint festgelegt. Dann wird geprüft, ob die Abschaltschwelle erreicht wurde.
        """
        mode = mode_tuple[0]
        submode = mode_tuple[1]
        prio = mode_tuple[2]
        # LP, der abgeschaltet werden soll
        preferenced_chargepoints = []
        # enthält alle LP, auf die das Tupel zutrifft
        valid_chargepoints = {}
        for cp in data.data.cp_data:
            if isinstance(cp, Chargepoint):
                try:
                    # chargestate, weil nur die geprüft werden sollen, die tatsächlich laden und nicht die, die in
                    # diesem Zyklus eingeschaltet wurden.
                    if not cp.data["get"]["charge_state"]:
                        continue
                    if cp.data["set"]["charging_ev"] != -1:
                        charging_ev = cp.data["set"]["charging_ev_data"]
                        if((charging_ev.charge_template.data["prio"] == prio) and
                            (charging_ev.charge_template.data["chargemode"]["selected"] == mode or mode is None) and
                                (charging_ev.data["control_parameter"]["submode"] == submode)):
                            valid_chargepoints[cp] = None
                except Exception:
                    log.exception(f"Fehler im Algorithmus-Modul für Ladepunkt{cp.cp_num}")
        preferenced_chargepoints = self._get_preferenced_chargepoint(
            valid_chargepoints, False)

        if len(preferenced_chargepoints) == 0:
            # Es gibt keine Ladepunkte in diesem Lademodus, die noch nicht laden oder die noch gestoppt werden können.
            return
        else:
            # Solange die Liste durchgehen, bis die Abschaltschwelle nicht mehr erreicht wird.
            for cp in preferenced_chargepoints:
                try:
                    if cp.data["set"]["current"] != 0:
                        data.data.pv_data["all"].switch_off_check_threshold(
                            cp, self._get_bat_and_evu_overhang())
                except Exception:
                    log.exception(f"Fehler im Algorithmus-Modul für Ladepunkt{cp.cp_num}")

    def _check_auto_phase_switch_delay(self) -> None:
        """ geht alle LP durch und prüft, ob eine Ladung aktiv ist, ob automatische Phasenumschaltung
        möglich ist und ob ob ein Timer gestartet oder gestoppt werden muss oder ob ein Timer abgelaufen ist.
        """
        for cp in data.data.cp_data.values():
            if isinstance(cp, Chargepoint):
                try:
                    if cp.data["set"]["charging_ev"] != -1:
                        charging_ev = cp.data["set"]["charging_ev_data"]
                        if (cp.data["config"]["auto_phase_switch_hw"] and
                                cp.data["get"]["charge_state"] and
                                charging_ev.data["control_parameter"]["chargemode"] == "pv_charging" and
                                data.data.general_data["general"].get_phases_chargemode("pv_charging") == 0 and
                                charging_ev.data["control_parameter"]["timestamp_perform_phase_switch"] == "0"):
                            # Gibt die Stromstärke und Phasen zurück, mit denen nach der Umschaltung geladen werden
                            # soll. Falls keine Umschaltung erforderlich ist, werden Strom und Phasen, die übergeben
                            # wurden, wieder zurückgegeben.
                            log.debug("Ladepunkt "+str(cp) +
                                      ": Prüfen, ob Phasenumschaltung durchgeführt werden soll.")
                            phases, current, message = charging_ev.auto_phase_switch(
                                cp.cp_num, charging_ev.data["control_parameter"]["required_current"],
                                charging_ev.data["control_parameter"]["phases"],
                                cp.data["get"]["currents"])
                            if message is not None:
                                cp.data["get"]["state_str"] = message
                            # Nachdem im Automatikmodus die Anzahl Phasen bekannt ist, Einhaltung des Maximalstroms
                            # prüfen.
                            required_current = charging_ev.check_min_max_current(
                                current, charging_ev.data["control_parameter"]["phases"])
                            charging_ev.data["control_parameter"]["required_current"] = required_current
                            Pub().pub("openWB/set/vehicle/"+str(charging_ev.ev_num) +
                                      "/control_parameter/required_current", required_current)
                            charging_ev.data["control_parameter"]["phases"] = phases
                            Pub().pub("openWB/set/vehicle/"+str(charging_ev.ev_num) +
                                      "/control_parameter/phases", phases)
                            self._process_data(cp, current)
                except Exception:
                    log.exception(f"Fehler im Algorithmus-Modul für Ladepunkt{cp.cp_num}")

    def _manage_distribution(self) -> None:
        """ verteilt den EVU-Überschuss und den maximalen Bezug auf die Ladepunkte, die dem Modus im Tupel entsprechen.
        Die Funktion endet, wenn das Lastmanagement eingereift oder keine Ladepunkte mehr in diesem Modus vorhanden
        sind. Die Zuteilung erfolgt gemäß der Reihenfolge in _get_preferenced_chargepoint.
        """
        try:
            log.info("## Zuteilung des Überschusses")
            for mode_tuple in self.chargemodes:
                try:
                    mode = mode_tuple[0]
                    submode = mode_tuple[1]
                    prio = mode_tuple[2]
                    preferenced_chargepoints = []
                    # enthält alle LP, auf die das Tupel zutrifft
                    valid_chargepoints = {}
                    for cp in data.data.cp_data.values():
                        if isinstance(cp, Chargepoint):
                            if cp.data["set"]["charging_ev"] != -1:
                                charging_ev = cp.data["set"]["charging_ev_data"]
                                # set-> current enthält einen Wert, wenn das EV in diesem Zyklus eingeschaltet werden
                                # soll, aktuell aber noch nicht lädt.
                                if "current" in cp.data["set"]:
                                    if (cp.data["set"]["current"] != 0 or
                                            charging_ev.data["control_parameter"]["required_current"] == 0):
                                        continue
                                if((charging_ev.charge_template.data["prio"] == prio) and
                                   (charging_ev.charge_template.data["chargemode"]["selected"] == mode or
                                    mode is None) and
                                        (charging_ev.data["control_parameter"]["submode"] == submode)):
                                    valid_chargepoints[cp] = None
                    preferenced_chargepoints = self._get_preferenced_chargepoint(
                        valid_chargepoints, True)

                    if len(preferenced_chargepoints) != 0:
                        log.debug("Zuteilung für Ladepunkte " +
                                  str([cp.cp_num for cp in preferenced_chargepoints]) +
                                  " in Lademodus "+str(mode)+" Submodus "+str(submode)+" Prio "+str(prio))
                        current_mode_index = self.chargemodes.index(mode_tuple)
                        self._distribute_power_to_cp(
                            preferenced_chargepoints, current_mode_index)
                except Exception:
                    log.exception(f"Fehler im Algorithmus-Modul für Modus {mode_tuple}")
            else:
                # kein Ladepunkt, der noch auf Zuteilung wartet
                log.info("## Zuteilung beendet, da kein Ladepunkt mehr auf Zuteilung wartet.")
        except Exception:
            log.exception("Fehler im Algorithmus-Modul")

    def _distribute_power_to_cp(self,
                                preferenced_chargepoints: List[Chargepoint],
                                current_mode_index: int) -> None:
        """ Ladepunkte, die eingeschaltet werden sollen, durchgehen.
        """
        for chargepoint in preferenced_chargepoints:
            try:
                charging_ev = chargepoint.data["set"]["charging_ev_data"]
                phases = charging_ev.data["control_parameter"]["phases"]
                required_current = charging_ev.data["control_parameter"]["required_current"]
                required_power = phases * 230 * \
                    charging_ev.data["control_parameter"]["required_current"]
                Pub().pub("openWB/set/chargepoint/"+str(chargepoint.cp_num) +
                          "/set/required_power", required_power)
                chargepoint.data["set"]["required_power"] = required_power
                if charging_ev.data["control_parameter"]["submode"] == "pv_charging":
                    self._calc_pv_charging(
                        chargepoint, required_current, phases, current_mode_index)
                elif (charging_ev.data["control_parameter"]["submode"] == "stop" or
                        (charging_ev.data["control_parameter"]["submode"] == "standby")):
                    required_current = 0
                    self._process_data(chargepoint, required_current)
                else:
                    self._calc_normal_load(
                        chargepoint, required_current, phases, current_mode_index)
            except Exception:
                log.exception("Fehler im Algorithmus-Modul für Ladepunkt"+chargepoint.cp_num)

    def _calc_normal_load(self,
                          chargepoint: Chargepoint,
                          required_current: float,
                          phases: int,
                          current_mode_index: int) -> None:
        """ prüft, ob mit PV geladen werden kann oder bezogen werden muss. Falls erforderlich LP mit niedrigerer
        Ladepriorität reduzieren/abschalten, um LP laden. Ladepunkte mit gleichem Lademodus und gleicher Priorität
        dürfen nur reduziert, aber nicht abgeschaltet werden.
        """
        try:
            evu_counter = data.data.counter_data["all"].get_evu_counter()
            # aktuelle Werte speichern (werden wieder hergestellt, wenn das Lastmanagement die Ladung verhindert)
            counter_data_old = copy.deepcopy(data.data.counter_data)
            pv_data_old = copy.deepcopy(data.data.pv_data)
            bat_data = copy.deepcopy(data.data.bat_data)
            cp_data_old = copy.deepcopy(data.data.cp_data)

            # Wenn bereits geladen wird, nur die Änderung zuteilen
            current_to_allocate = required_current
            max_used_current = max(chargepoint.data["get"]["currents"])
            if max_used_current != 0:
                current_to_allocate -= max_used_current

            log.debug("Benötigter neuer/zusätzlicher Strom "+str(current_to_allocate)+"A")
            _, overloaded_counters = allocate_power(chargepoint, current_to_allocate, phases)
            self._process_data(chargepoint, required_current)

            if data.data.counter_data["all"].data["set"]["loadmanagement_active"] and len(overloaded_counters) != 0:
                # Lastmanagement hat eingegriffen
                log.debug("Aktuell kalkulierte Ströme am EVU-Punkt[A]: "+str(
                    data.data.counter_data[evu_counter].data["set"].get("currents_used")))
                log.warning(
                    "Für die Ladung an LP"+str(chargepoint.cp_num) +
                    " muss erst ein Ladepunkt mit gleicher/niedrigerer Priorität reduziert/gestoppt werden.")
                data.data.counter_data[evu_counter].print_stats()
                # Zähler mit der größten Überlastung ermitteln
                overloaded_counters = sorted(
                    overloaded_counters.items(), key=lambda e: e[1][1], reverse=True)
                # Ergebnisse des Lastmanagements holen, das beim Einschalten durchgeführt worden ist. Es ist
                # ausreichend, Zähler mit der größten Überlastung im Pfad zu betrachten. Kann diese nicht eliminiert
                # werden, kann der Ladepunkt nicht laden.
                chargepoints = data.data.counter_data["all"].get_chargepoints_of_counter(
                    overloaded_counters[0][0])
                remaining_current_overshoot = overloaded_counters[0][1][0]
                # LP mit niedrigerer Priorität reduzieren und ggf. stoppen
                for mode in reversed(self.chargemodes[(current_mode_index+1):-4]):
                    try:
                        # Runterregeln
                        remaining_current_overshoot = self._down_regulation(
                            mode,
                            chargepoints,
                            remaining_current_overshoot,
                            overloaded_counters[0][1][1],
                            prevent_stop=True)
                        if remaining_current_overshoot <= 0:
                            # LP kann nun wie gewünscht eingeschaltet werden
                            self._process_data(
                                chargepoint, chargepoint.data["set"]["charging_ev_data"].data["control_parameter"]
                                ["required_current"])
                            break
                        else:
                            # Abschalten
                            if not chargepoint.data["set"]["charging_ev_data"].ev_template.data[
                                    "prevent_switch_stop"]:
                                remaining_current_overshoot = self._down_regulation(
                                    mode, chargepoints,
                                    remaining_current_overshoot,
                                    overloaded_counters[0][1][1],
                                    prevent_stop=False)
                                if remaining_current_overshoot <= 0:
                                    # LP kann nun wie gewünscht eingeschaltet werden
                                    self._process_data(
                                        chargepoint,
                                        chargepoint.data["set"]["charging_ev_data"].data["control_parameter"][
                                            "required_current"])
                                    break
                    except Exception:
                        log.exception("Fehler im Algorithmus-Modul für Modus "+str(mode))
                else:
                    # Ladepunkt, der gestartet werden soll reduzieren
                    remaining_current_overshoot = self._perform_down_regulation(
                        [chargepoint], remaining_current_overshoot, overloaded_counters[0][1][1], prevent_stop=True)
                    # Ladepunkte mit gleicher Priorität reduzieren. Diese dürfen nicht gestoppt werden.
                    if remaining_current_overshoot != 0:
                        remaining_current_overshoot = self._down_regulation(
                            self.chargemodes[current_mode_index],
                            chargepoints, remaining_current_overshoot, overloaded_counters[0][1][1],
                            prevent_stop=True)
                    if remaining_current_overshoot != 0:
                        # Ladepunkt darf nicht laden
                        # Zustand von vor dem Lastmanagement wieder herstellen
                        data.data.counter_data = counter_data_old
                        data.data.pv_data = pv_data_old
                        data.data.bat_data = bat_data
                        data.data.cp_data = cp_data_old
                        # Beim Wiederherstellen der Kopie wird die Adresse der Kopie zugewiesen, sodass die Adresse des
                        # LP aktualisiert werden muss,
                        # um Änderungen in der Klasse vorzunehmen, die das data-Modul referenziert.
                        chargepoint = data.data.cp_data[f"cp{chargepoint.cp_num}"]
                        # keine weitere Zuteilung
                        message = "Keine Ladung, da das Reduzieren/Abschalten der anderen Ladepunkte nicht ausreicht."
                        log.info("LP "+str(chargepoint.cp_num)+": "+message)
                        log.debug("Wiederherstellen des Zustands, bevor LP" +
                                  str(chargepoint.cp_num)+" betrachtet wurde.")
                        chargepoint.data["get"]["state_str"] = message
                        self._process_data(chargepoint, 0)
            else:
                (log.info(
                    "LP: " + str(chargepoint.cp_num) + ", Ladestrom: " + str(chargepoint.data["set"]["current"]) +
                    "A, Phasen: " +
                    str(chargepoint.data["set"]["charging_ev_data"].data["control_parameter"]["phases"]) +
                    ", Ladeleistung: " +
                    str(
                        (chargepoint.data["set"]["charging_ev_data"].data["control_parameter"]["phases"] *
                         chargepoint.data["set"]["current"] * 230)) + "W"))
            data.data.counter_data[evu_counter].print_stats()
        except Exception:
            log.exception("Fehler im Algorithmus-Modul")

    def _calc_pv_charging(self,
                          chargepoint: Chargepoint,
                          required_current: float,
                          phases: int,
                          current_mode_index: int) -> None:
        """prüft, ob Speicher oder EV Vorrang hat und wie viel Strom/Leistung genutzt werden kann.
        """
        try:
            # Wenn bereits geladen wird, nur die Änderung zuteilen
            current_to_allocate = required_current
            max_used_current = max(chargepoint.data["get"]["currents"])
            if max_used_current != 0:
                current_to_allocate -= max_used_current

            if not self._check_cp_without_feed_in_is_prioritised(chargepoint):
                self._process_data(chargepoint, 0)
                return

            allocated_current, threshold_reached = data.data.pv_data["all"].switch_on(
                chargepoint,
                current_to_allocate,
                phases,
                data.data.bat_data["all"].power_for_bat_charging())
            if threshold_reached:
                set_current = max_used_current + allocated_current
            else:
                set_current = 0
                # Zustand merken
                pv_data_old = copy.deepcopy(data.data.pv_data)
                cp_data_old = copy.deepcopy(data.data.cp_data)
                # LP mit niedrigerer Priorität abschalten (Reduktion ist bereits zu Beginn des Zyklus erfolgt)
                for mode_tuple in reversed(self.chargemodes[current_mode_index+1:-4]):
                    mode = mode_tuple[0]
                    submode = mode_tuple[1]
                    prio = mode_tuple[2]
                    preferenced_chargepoints = []
                    # enthält alle LP, auf die das Tupel zutrifft
                    valid_chargepoints = {}
                    for item in data.data.cp_data:
                        try:
                            if "cp" in item:
                                cp = data.data.cp_data[item]
                                if cp.data["set"]["charging_ev"] != -1:
                                    charging_ev = cp.data["set"]["charging_ev_data"]
                                    # set-> current enthält einen Wert, wenn das EV in diesem Zyklus eingeschaltet
                                    # werden soll, aktuell aber noch nicht lädt.
                                    if "current" in cp.data["set"]:
                                        if cp.data["set"]["current"] == 0:
                                            continue
                                    if((charging_ev.charge_template.data["prio"] == prio) and
                                       (charging_ev.charge_template.data["chargemode"]["selected"] == mode or
                                        mode is None) and
                                            (charging_ev.data["control_parameter"]["submode"] == submode)):
                                        valid_chargepoints[cp] = None
                        except Exception:
                            log.exception("Fehler im Algorithmus-Modul für Ladepunkt "+item)
                    preferenced_chargepoints = self._get_preferenced_chargepoint(
                        valid_chargepoints, False)
                    if preferenced_chargepoints:
                        for cp in preferenced_chargepoints:
                            try:
                                # abschalten
                                if not cp.data["set"]["charging_ev_data"].ev_template.data["prevent_switch_stop"]:
                                    data.data.pv_data["all"].allocate_evu_power(
                                        -1 * cp.data["set"]["charging_ev_data"].data["control_parameter"]
                                        ["required_current"] * 230 * chargepoint.data["get"]["phases_in_use"])
                                    self._process_data(cp, 0)
                                    log.warning(
                                        "LP" + str(cp.cp_num) + " abgeschaltet, um die Einschaltverzögerung an LP" +
                                        str(chargepoint.cp_num) + " zu starten.")
                                    # switch_on erneut durchführen
                                    allocated_current, threshold_reached = data.data.pv_data["all"].switch_on(
                                        chargepoint,
                                        required_current,
                                        phases,
                                        data.data.bat_data["all"].power_for_bat_charging())
                                    if threshold_reached:
                                        set_current = max_used_current + allocated_current
                                        break
                            except Exception:
                                log.exception(f"Fehler im Algorithmus-Modul für Ladepunkt{cp.cp_num}")
                        if threshold_reached:
                            break
                else:
                    # Es konnte nicht genug Leistung freigegeben werden.
                    data.data.pv_data = pv_data_old
                    data.data.cp_data = cp_data_old
                    log.info("Keine Ladung an LP"+str(chargepoint.cp_num) +
                             ", da das Reduzieren/Abschalten der anderen Ladepunkte nicht ausreicht.")
                    log.debug("Wiederherstellen des Zustands, bevor LP" +
                              str(chargepoint.cp_num)+" betrachtet wurde.")
            self._process_data(chargepoint, set_current)
        except Exception:
            log.exception("Fehler im Algorithmus-Modul")

    def _distribute_unused_evu_overhang(self) -> None:
        """ prüft die Lademodi, die mit EVU-Überschuss laden, in absteigender Reihenfolge, ob für LP ohne
        Einspeisegrenze noch EVU-Überschuss übrig ist und dann für die LP mit Einspeisegrenze.
        """
        try:
            log.info("## Übrigen Überschuss verteilen.")
            for mode in self.chargemodes[6:-4]:
                overhang = self._get_bat_and_evu_overhang()
                if overhang != 0:
                    if overhang > 0.01:
                        self._distribute_remaining_overhang(mode, False)
                    if (overhang
                            - data.data.general_data["general"].data["chargemode_config"]["pv_charging"][
                                "feed_in_yield"]) > 0.01:
                        self._distribute_remaining_overhang(mode, True)
            data.data.pv_data["all"].put_stats()
        except Exception:
            log.exception("Fehler im Algorithmus-Modul")

    def _distribute_remaining_overhang(self, mode_tuple: Tuple[Optional[str], str, bool], feed_in_limit: bool) -> None:
        """ Verteilt den verbleibenden EVU-Überschuss gleichmäßig auf alle mit EVU-Überschuss ladenden EV. Dazu wird
        zunächst die Anzahl der EV ermittelt. Danach wird der Überschuss pro Phase, über die das EV lädt, ermittelt
        und auf die Phasen aufgeschlagen.
        """
        try:
            num_of_ev = 0
            mode = mode_tuple[0]
            submode = mode_tuple[1]
            prio = mode_tuple[2]
            # Anzahl aller genutzten Phasen ermitteln
            for cp in data.data.cp_data.values():
                if isinstance(cp, Chargepoint):
                    try:
                        if cp.data["set"]["charging_ev"] != -1:
                            charging_ev = cp.data["set"]["charging_ev_data"]
                            if (((charging_ev.charge_template.data["prio"] == prio) and
                                    (charging_ev.charge_template.data["chargemode"]["selected"] == mode or
                                     mode is None) and
                                    (charging_ev.data["control_parameter"]["submode"] == submode)) and
                                    cp.data["set"]["current"] != 0):
                                # Erst hochregeln, wenn geladen wird.
                                if ((cp.data["set"]["current"]
                                        - charging_ev.ev_template.data["nominal_difference"])
                                        < max(cp.data["get"]["currents"]) and
                                        charging_ev.charge_template.data["chargemode"]["pv_charging"][
                                            "feed_in_limit"] == feed_in_limit):
                                    # Ev dieser Prioritätsstufe zählen
                                    num_of_ev += 1
                    except Exception:
                        log.exception(f"Fehler im Algorithmus-Modul für Ladepunkt{cp.cp_num}")
            # Ladung aktiv?
            if num_of_ev > 0:
                new_current = 0
                diff_per_ev_power = 0
                dif_per_ev_current = 0
                bat_overhang = data.data.bat_data["all"].power_for_bat_charging(
                )
                if not feed_in_limit:
                    diff_per_ev_power = (
                        data.data.pv_data["all"].overhang_left() + bat_overhang) / num_of_ev
                else:
                    feed_in_yield = data.data.general_data["general"].data[
                        "chargemode_config"]["pv_charging"]["feed_in_yield"]
                    if data.data.pv_data["all"].overhang_left() <= feed_in_yield:
                        diff_per_ev_power = (data.data.pv_data["all"].overhang_left(
                        ) - feed_in_yield + bat_overhang) / num_of_ev
                        log.debug("diff_per_ev_power "+str(diff_per_ev_power))
                    else:
                        # Wenn die Einspeisegrenze erreicht wird, Strom schrittweise erhöhen (1A pro Phase), bis
                        # dies nicht mehr der Fall ist.
                        dif_per_ev_current = 1
                        log.debug("dif_per_ev_current "+str(dif_per_ev_current))
                if diff_per_ev_power > 0 or dif_per_ev_current > 0:
                    for cp in data.data.cp_data.values():
                        if isinstance(cp, Chargepoint):
                            try:
                                if cp.data["set"]["charging_ev"] != -1:
                                    charging_ev = cp.data["set"]["charging_ev_data"]
                                    if ((charging_ev.charge_template.data["prio"] == prio and
                                            (charging_ev.charge_template.data["chargemode"]["selected"] == mode or
                                             mode is None) and
                                            charging_ev.data["control_parameter"]["submode"] == submode) and
                                            cp.data["set"]["current"] != 0):
                                        if ((cp.data["set"]["current"]
                                                - charging_ev.ev_template.data["nominal_difference"])
                                                < max(cp.data["get"]["currents"]) and
                                                charging_ev.charge_template.data["chargemode"]["pv_charging"][
                                                    "feed_in_limit"] == feed_in_limit):
                                            if cp.data["get"]["charge_state"]:
                                                phases = cp.data["get"]["phases_in_use"]
                                            else:
                                                phases = cp.data["set"]["charging_ev_data"].data[
                                                    "control_parameter"]["phases"]
                                            if diff_per_ev_power != 0:
                                                new_current = ((
                                                    diff_per_ev_power / 230 / phases)
                                                    + cp.data["set"]["current"])
                                            else:
                                                new_current = dif_per_ev_current + \
                                                    cp.data["set"]["current"]
                                            log.debug(
                                                "new_current "+str(new_current)+"phases "+str(phases))
                                            # Um max. 5A pro Zyklus regeln
                                            if ((-5-charging_ev.ev_template.data["nominal_difference"])
                                                    < (new_current - max(cp.data["get"]["currents"]))
                                                    < (5+charging_ev.ev_template.data["nominal_difference"])):
                                                current = new_current
                                                log.debug("current 1 "+str(current))
                                            else:
                                                if new_current < max(cp.data["get"]["currents"]):
                                                    current = max(
                                                        cp.data["get"]["currents"]) - 5
                                                    log.debug("current 2 "+str(current))
                                                else:
                                                    current = max(
                                                        cp.data["get"]["currents"]) + 5
                                                    log.debug("current 3 "+str(current))
                                            # Einhalten des Mindeststroms des Lademodus und Maximalstroms des EV
                                            current = charging_ev.check_min_max_current(
                                                current, phases, pv=True)
                                            current_diff = current - cp.data["set"]["current"]
                                            power_diff = phases * 230 * \
                                                (current -
                                                 cp.data["set"]["current"])
                                            log.debug("power_diff "+str(power_diff)+"current " +
                                                      str(current))
                                            log.debug("max get current " +
                                                      str(max(cp.data["get"]["currents"])))

                                            if power_diff != 0:
                                                # Laden nur mit der Leistung, die vorher der Speicher bezogen hat
                                                if bat_overhang > 0 and power_diff > 0:
                                                    if (bat_overhang - power_diff) > 0:
                                                        missing_current = use_evu_bat_power(
                                                            cp,
                                                            current_diff,
                                                            phases,
                                                            pv_mode=False)
                                                    # Laden mit EVU-Überschuss und der Leistung, die vorher der
                                                    # Speicher bezogen hat
                                                    else:
                                                        pv_current_diff = (power_diff - bat_overhang) / 230 / phases
                                                        missing_current = use_evu_bat_power(
                                                            cp, pv_current_diff, phases, pv_mode=True)
                                                        missing_current = use_evu_bat_power(
                                                            cp,
                                                            bat_overhang / 230 / phases,
                                                            phases,
                                                            pv_mode=False)
                                                # Laden nur mit EVU-Überschuss bzw. Reduktion des EVU-Bezugs
                                                else:
                                                    missing_current = use_evu_bat_power(
                                                        cp, current_diff, phases, pv_mode=True)
                                            else:
                                                missing_current = 0

                                            log.debug(f"missing_current {missing_current}")
                                            cp.data["set"]["current"] = current + missing_current
                                            log.info("Überschussladen an LP: " + str(cp.cp_num) +
                                                     ", Ladestrom: " + str(current) + "A, Phasen: " +
                                                     str(phases) + ", Ladeleistung: " +
                                                     str(phases * 230 * current) + "W")
                            except Exception:
                                log.exception(f"Fehler im Algorithmus-Modul für Ladepunkt{cp.cp_num}")
        except Exception:
            log.exception("Fehler im Algorithmus-Modul")

    def _stop_after_switch_off_delay(self) -> None:
        for cp in data.data.cp_data.values():
            if isinstance(cp, Chargepoint):
                try:
                    if cp.data["set"]["charging_ev"] != -1:
                        if (cp.data["set"]["charging_ev_data"].data["control_parameter"]["submode"] ==
                                "pv_charging" and cp.data["get"]["charge_state"]):
                            if data.data.pv_data["all"].switch_off_check_timer(cp):
                                # Ladung stoppen
                                required_current = 0
                                self._process_data(
                                    cp, required_current)
                                # in diesem Durchgang soll kein Strom zugeteilt werden
                                cp.data["set"]["charging_ev_data"].data["control_parameter"][
                                    "submode"] = "stop"
                except Exception:
                    log.exception(f"Fehler im Algorithmus-Modul für Ladepunkt{cp.cp_num}")

    # Helperfunctions

    def _get_preferenced_chargepoint(self, valid_chargepoints: Dict[Chargepoint, None], start_charging: bool):
        """ermittelt aus dem Dictionary den Ladepunkt, der eindeutig die Bedingung erfüllt. Die Bedingungen sind:
        geringste Mindeststromstärke, niedrigster SoC, frühester Ansteck-Zeitpunkt(Einschalten)/Lademenge(Abschalten),
        niedrigste Ladepunktnummer.
        Parameter
        ---------
        valid_chargepoints: dict
            enthält alle Ladepunkte gleicher Priorität und Lademodus, die noch nicht laden und keine Zuteilung haben.
        start: bool
            Soll die Ladung gestoppt oder gestartet werden?

        Return
        ------
        preferenced_chargepoints: list
            Liste der Ladepunkte in der Reihenfolge, in der sie geladen/gestoppt werden sollen.
        """
        preferenced_chargepoints = []
        try:
            # Bedingungen in der Reihenfolge, in der sie geprüft werden. 3. Bedingung, ist abhängig davon, ob ein- oder
            # ausgeschaltet werden soll.
            if start_charging:
                condition_types = ("min_current", "soc", "plug_in", "cp_num")
            else:
                condition_types = ("min_current", "soc",
                                   "charged_since_plugged", "cp_num")
            # Bedingung, die geprüft wird (entspricht Index von condition_types)
            condition = 0
            if valid_chargepoints:
                while len(valid_chargepoints) > 0:
                    # entsprechend der Bedingung die Values im Dictionary füllen
                    if condition_types[condition] == "min_current":
                        valid_chargepoints.update(
                            (cp, cp.data["set"]["charging_ev_data"].data["control_parameter"]["required_current"])
                            for cp, val in valid_chargepoints.items())
                    elif condition_types[condition] == "soc":
                        valid_chargepoints.update(
                            (cp, cp.data["set"]["charging_ev_data"].data["get"]["soc"]) for cp,
                            val in valid_chargepoints.items())
                    elif condition_types[condition] == "plug_in":
                        valid_chargepoints.update(
                            (cp, cp.data["set"]["plug_time"]) for cp, val in valid_chargepoints.items())
                    elif condition_types[condition] == "charged_since_plugged":
                        valid_chargepoints.update(
                            (cp, cp.data["set"]["log"]["charged_since_plugged_counter"]) for cp,
                            val in valid_chargepoints.items())
                    else:
                        valid_chargepoints.update(
                            (cp, cp.cp_num) for cp, val in valid_chargepoints.items())

                    if start_charging:
                        # kleinsten Value im Dictionary ermitteln
                        extreme_value = min(valid_chargepoints.values())
                    else:
                        extreme_value = max(valid_chargepoints.values())
                    # dazugehörige Keys ermitteln
                    extreme_cp = [
                        key for key in valid_chargepoints if valid_chargepoints[key] == extreme_value]
                    if len(extreme_cp) > 1:
                        # Wenn es mehrere LP gibt, die den gleichen Minimalwert haben, nächste Bedingung prüfen.
                        condition += 1
                    else:
                        preferenced_chargepoints.append(extreme_cp[0])
                        valid_chargepoints.pop(extreme_cp[0])

            return preferenced_chargepoints
        except Exception:
            log.exception("Fehler im Algorithmus-Modul")
            return preferenced_chargepoints

    def _check_cp_without_feed_in_is_prioritised(self, chargepoint: Chargepoint) -> bool:
        """ Wenn ein LP im Submodus PV-Laden nicht die Maximalstromstärke zugeteilt bekommen hat,
        darf ein LP mit Einspeisegrenze nicht eingeschaltet werden.
        Diese Funktion wird benötigt, da sie während der Verteilung des Überschusses aufgerufen
        wird. Der verbleibende Überschuss wird erst später verteilt, wenn bereits der LP mit
        Einspeisegrenze eine Ladefreigabe erhalten hätte.

        Return
        ------
        True: LP darf geladen werden.
        False: LP mit Einspeisegrenze darf nicht geladen werden.
        """
        try:
            if chargepoint.data["set"]["charging_ev_data"].charge_template.data["chargemode"]["pv_charging"][
                    "feed_in_limit"]:
                for cp in data.data.cp_data.values():
                    if isinstance(cp, Chargepoint):
                        try:
                            if cp.data["set"]["charging_ev"] != -1:
                                charging_ev = cp.data["set"]["charging_ev_data"]
                                if (charging_ev.data["control_parameter"]["submode"] == "pv_charging" and
                                        not charging_ev.charge_template.data["chargemode"]["pv_charging"][
                                            "feed_in_limit"]):
                                    if cp.data["set"]["charging_ev_data"].data["control_parameter"][
                                            "phases"] == 1:
                                        max_current = charging_ev.ev_template.data["max_current_one_phase"]
                                    else:
                                        max_current = charging_ev.ev_template.data["max_current_multi_phases"]
                                    if cp.data["set"]["current"] != max_current:
                                        return False
                        except Exception:
                            log.exception(f"Fehler im Algorithmus-Modul für Ladepunkt{cp.cp_num}")
            return True
        except Exception:
            log.exception("Fehler im Algorithmus-Modul")
            return True

    def _process_data(self, chargepoint: Chargepoint, required_current: float) -> None:
        """ setzt die ermittelte Anzahl Phasen, Stromstärke und Leistung in den Dictionaries,
        veröffentlicht sie und schreibt sie ins Log.

        Parameter
        ---------
        chargepoint: dict
            Daten des Ladepunkts
        required_current: float
            Stromstärke, mit der geladen werden soll
        """
        try:
            chargepoint.data["set"]["current"] = required_current
            data.data.pv_data["all"].put_stats()
        except Exception:
            log.exception("Fehler im Algorithmus-Modul")

    def _get_bat_and_evu_overhang(self) -> float:
        """ ermittelt den verfügbaren Überhang. Da zu Beginn des Algorithmus die Leistung, die über der benötigten
        Leistung liegt, freigegeben wird, muss der verbleibende EVU-Überhang betrachtet werden. Erst wenn nicht mehr
        genug freigegeben (und am Ende wieder zugeteilt wird) muss abgeschaltet werden.
        """
        try:
            return data.data.bat_data["all"].power_for_bat_charging() + data.data.pv_data["all"].overhang_left()
        except Exception:
            log.exception("Fehler im Algorithmus-Modul")
            return 0


def allocate_power(chargepoint: Chargepoint,
                   required_current: float,
                   phases: int) -> Tuple[float, Dict[str, Tuple[float, int]]]:
    """ zugeteilt, wenn vorhanden erst Speicherladeleistung, dann EVU-Überschuss
    und dann EVU-Bezug im Lastmanagement.
    """
    try:
        bat_overhang = data.data.bat_data["all"].power_for_bat_charging()
        evu_overhang = data.data.pv_data["all"].overhang_left()
        remaining_required_power = required_current*phases*230
        required_power = remaining_required_power
        overloaded_counters = {}
        # Wenn vorhanden, Speicherenergie zuteilen.
        if bat_overhang > 0:
            if bat_overhang < required_power:
                to_allocate = bat_overhang
                remaining_required_power = required_power - bat_overhang
            else:
                to_allocate = required_power
                remaining_required_power = 0
            missing_current = use_evu_bat_power(chargepoint, to_allocate / (phases * 230), phases, pv_mode=False)
            if missing_current:
                required_current += missing_current
        # Wenn vorhanden, EVU-Überschuss zuteilen.
        if remaining_required_power > 0:
            if evu_overhang > 0:
                if evu_overhang < required_power:
                    to_allocate = evu_overhang
                    remaining_required_power = required_power - evu_overhang
                else:
                    to_allocate = required_power
                    remaining_required_power = 0
                missing_current = use_evu_bat_power(chargepoint, to_allocate / (phases * 230), phases, pv_mode=True)
                if missing_current:
                    required_current += missing_current
        # Rest ermitteln und zuteilen
        if remaining_required_power > 0:
            evu_current = remaining_required_power / (phases * 230)
            loadmanagement_state, overloaded_counters = loadmanagement.loadmanagement_for_cp(
                chargepoint, evu_current, phases)
            if loadmanagement_state:
                required_current = 0
        return required_current, overloaded_counters
    except Exception:
        log.exception("Fehler im Algorithmus-Modul")
        return 0, {}


def use_evu_bat_power(chargepoint: Chargepoint,
                      current_diff: float,
                      phases: int,
                      pv_mode: bool = True) -> float:
    """ prüft bei der Nutzung von Speicher-Leistung oder EVU-Überschuss, ob genug Leistung vorhanden ist und ob
    genügend Leistung/Strom vom Lastmanagement zur Verfügung steht. Das ist erforderlich, da mehrere LP an derselben
    Phase laden können und dann insgesamt zwar genug Überschuss vorhanden ist, aber nicht unbedingt auf der benötigten
    Phase.
    Wenn das Lastmanagement aktiv wird, wird der fehlende Strom dem Lastamanagement entnommen und zurückgegeben.
    """
    power_diff = current_diff * phases * 230
    if pv_mode:
        return_power = data.data.pv_data["all"].allocate_evu_power(
            power_diff)
    else:
        return_power = data.data.bat_data["all"].allocate_bat_power(
            power_diff)
    power_diff = power_diff-return_power
    current_diff = current_diff - return_power / phases / 230
    loadmanagement_state, overloaded_counters = loadmanagement.loadmanagement_for_cp(
        chargepoint, current_diff, phases)
    if loadmanagement_state:
        overloaded_counters = sorted(
            overloaded_counters.items(), key=lambda e: e[1][1], reverse=True)
        # Wenn max_overshoot_phase -1 ist, wurde die maximale Gesamtleistung überschritten und
        # max_current_overshoot muss, wenn weniger als 3 Phasen genutzt werden, entsprechend multipliziert
        # werden.
        if overloaded_counters[0][1][1] == -1 and phases < 3:
            missing_current = (
                overloaded_counters[0][1][0] * (3 - phases + 1)) * -1
        else:
            missing_current = overloaded_counters[0][1][0] * -1
        loadmanagement.loadmanagement_for_cp(
            chargepoint, missing_current, phases)
        return missing_current
    return 0
