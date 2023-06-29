"""Zähler-Logik
"""
from dataclasses import dataclass, field
import logging
import operator
from typing import List, Tuple

from control import data
from control.ev import Ev
from control.chargepoint.chargepoint import Chargepoint
from control.chargepoint.chargepoint_state import ChargepointState
from dataclass_utils.factories import currents_list_factory, voltages_list_factory
from helpermodules import timecheck
from helpermodules.phase_mapping import convert_cp_currents_to_evu_currents
from helpermodules.pub import Pub
from modules.common.fault_state import FaultStateLevel

log = logging.getLogger(__name__)


def get_counter_default_config():
    return {"max_currents": [16, 16, 16],
            "max_total_power": 11000}


@dataclass
class Config:
    max_currents: List[float] = field(default_factory=currents_list_factory)
    max_total_power: float = 0


def config_factory() -> Config:
    return Config()


@dataclass
class Get:
    powers: List[float] = field(default_factory=currents_list_factory)
    currents: List[float] = field(default_factory=currents_list_factory)
    voltages: List[float] = field(default_factory=voltages_list_factory)
    power_factors: List[float] = field(default_factory=currents_list_factory)
    unbalanced_load: float = 0
    frequency: float = 0
    daily_exported: float = 0
    daily_imported: float = 0
    imported: float = 0
    exported: float = 0
    fault_state: int = 0
    fault_str: str = ""
    power: float = 0


def get_factory() -> Get:
    return Get()


@dataclass
class Set:
    error_counter: int = 0
    reserved_surplus: float = 0
    released_surplus: float = 0
    raw_power_left: float = 0
    raw_currents_left: List[float] = field(default_factory=currents_list_factory)
    surplus_power_left: float = 0
    state_str: str = ""


def set_factory() -> Set:
    return Set()


@dataclass
class CounterData:
    config: Config = field(default_factory=config_factory)
    get: Get = field(default_factory=get_factory)
    set: Set = field(default_factory=set_factory)


class Counter:
    MAX_EVU_ERRORS = 2

    def __init__(self, index):
        try:
            self.data = CounterData()
            self.num = index
        except Exception:
            log.exception("Fehler in der Zähler-Klasse von "+str(self.num))

    def setup_counter(self):
        # Zählvariablen vor dem Start der Regelung zurücksetzen
        try:
            self._set_loadmanagement_state()
            self._set_current_left()
            self._set_power_left()
            if self.data.get.fault_state == FaultStateLevel.ERROR:
                self.data.get.power = 0
                return
        except Exception:
            log.exception("Fehler in der Zähler-Klasse von "+str(self.num))

    # tested
    def _set_loadmanagement_state(self) -> None:
        # Wenn der Zähler keine Werte liefert, darf nicht geladen werden.
        connected_cps = data.data.counter_all_data.get_chargepoints_of_counter(f'counter{self.num}')
        loadmanagement_available = True
        if self.data.get.fault_state == FaultStateLevel.ERROR:
            self.data.set.error_counter += 1
            if self.data.set.error_counter >= self.MAX_EVU_ERRORS:
                loadmanagement_available = False
        else:
            self.data.set.error_counter = 0
        for cp in connected_cps:
            # Wird zu Beginn des Zyklus auf True gesetzt, wenn es einmal auf False gesetzt wird, darf es nicht wieder
            # auf True gesetzt werden.
            if loadmanagement_available is False:
                data.data.cp_data[cp].data.set.loadmanagement_available = loadmanagement_available
        Pub().pub(f"openWB/set/counter/{self.num}/set/error_counter", self.data.set.error_counter)

    # tested

    def _set_current_left(self) -> None:
        currents_raw = self.data.get.currents
        cp_keys = data.data.counter_all_data.get_chargepoints_of_counter(f"counter{self.num}")
        for cp_key in cp_keys:
            chargepoint = data.data.cp_data[cp_key]
            try:
                element_current = convert_cp_currents_to_evu_currents(
                    chargepoint.data.config.phase_1,
                    chargepoint.data.get.currents)
            except KeyError:
                element_current = [max(chargepoint.data.get.currents)]*3
            currents_raw = list(map(operator.sub, currents_raw, element_current))
        currents_raw = list(map(operator.sub, self.data.config.max_currents, currents_raw))
        if min(currents_raw) < 0:
            log.debug(f"Verbleibende Ströme: {currents_raw}, Überbelastung wird durch Hausverbrauch verursacht")
            currents_raw = [max(currents_raw[i], 0) for i in range(0, 3)]
        self.data.set.raw_currents_left = currents_raw
        log.info(f'Verbleibende Ströme an Zähler {self.num}: {self.data.set.raw_currents_left}A')

    # tested
    def get_unbalanced_load_exceeding(self, raw_currents_left: List[float]) -> List[float]:
        """gibt eine Liste zurück, die für jede Phase angibt, um wie viel Ampere die Schieflast überschritten wurde.
        So können gezielt Fahrzeuge reduziert werden, die auf dieser/n Phase(n) laden. Die Phase mit dem höchsten
        verfügbaren Strom (geringster vorhandener Strom) kann nicht beeinflusst werden, daher wird diese als Basis
        für die Berechnung verwendet."""
        max_exceeding = [0.0]*3
        if (f'counter{self.num}' == data.data.counter_all_data.get_evu_counter_str() and
                data.data.general_data.data.chargemode_config.unbalanced_load):
            for i in range(0, 3):
                unbalanced_load = max(raw_currents_left) - raw_currents_left[i]
                max_exceeding[i] = max(
                    unbalanced_load - data.data.general_data.data.chargemode_config.unbalanced_load_limit, 0)
        return max_exceeding

    def _set_power_left(self) -> None:
        if f'counter{self.num}' == data.data.counter_all_data.get_evu_counter_str():
            power_raw = self.data.get.power
            for cp in data.data.cp_data.values():
                power_raw -= cp.data.get.power
            self.data.set.raw_power_left = self.data.config.max_total_power - power_raw
            log.info(f'Verbleibende Leistung an Zähler {self.num}: {self.data.set.raw_power_left}W')
        else:
            self.data.set.raw_power_left = None

    def update_values_left(self, diffs) -> None:
        self.data.set.raw_currents_left = list(map(operator.sub, self.data.set.raw_currents_left, diffs))
        if self.data.set.raw_power_left:
            self.data.set.raw_power_left -= sum(diffs) * 230
        log.debug(f'Zähler {self.num}: {self.data.set.raw_currents_left}A verbleibende Ströme, '
                  f'{self.data.set.raw_power_left}W verbleibende Leistung')

    def update_surplus_values_left(self, diffs) -> None:
        self.data.set.raw_currents_left = list(map(operator.sub, self.data.set.raw_currents_left, diffs))
        if self.data.set.surplus_power_left:
            self.data.set.surplus_power_left -= sum(diffs) * 230
        log.debug(f'Zähler {self.num}: {self.data.set.raw_currents_left}A verbleibende Ströme, '
                  f'{self.data.set.surplus_power_left}W verbleibender Überschuss')

    def put_stats(self):
        try:
            if f'counter{self.num}' == data.data.counter_all_data.get_evu_counter_str():
                Pub().pub(f"openWB/set/counter/{self.num}/set/reserved_surplus",
                          self.data.set.reserved_surplus)
                Pub().pub(f"openWB/set/counter/{self.num}/set/released_surplus",
                          self.data.set.released_surplus)
                log.info(f'{self.data.set.reserved_surplus}W reservierte EVU-Leistung, '
                         f'{self.data.set.released_surplus}W freigegebene EVU-Leistung')
        except Exception:
            log.exception("Fehler in der Zähler-Klasse von "+str(self.num))

    def calc_surplus(self):
        # reservierte Leistung wird nicht berücksichtigt, weil diese noch verwendet werden kann, bis die EV
        # eingeschaltet werden. Es darf bloß nicht für zu viele zB die Einschaltverzögerung gestartet werden.
        evu_counter = data.data.counter_all_data.get_evu_counter()
        bat_surplus = data.data.bat_all_data.power_for_bat_charging()
        surplus = - evu_counter.data.get.power + bat_surplus
        ranged_surplus = self._control_range(surplus)
        log.info(f"Überschuss zur PV-geführten Ladung: {ranged_surplus}W")
        return ranged_surplus

    def calc_raw_surplus(self):
        # reservierte Leistung wird nicht berücksichtigt, weil diese noch verwendet werden kann, bis die EV
        # eingeschaltet werden. Es darf bloß nicht für zu viele zB die Einschaltverzögerung gestartet werden.
        evu_counter = data.data.counter_all_data.get_evu_counter()
        bat_surplus = data.data.bat_all_data.power_for_bat_charging()
        disengageable_smarthome_power = data.data.counter_all_data.data.set.disengageable_smarthome_power
        raw_power_left = evu_counter.data.set.raw_power_left
        max_power = evu_counter.data.config.max_total_power
        surplus = raw_power_left - max_power + bat_surplus + disengageable_smarthome_power
        ranged_surplus = max(self._control_range(surplus), 0)
        log.info(f"Überschuss zur PV-geführten Ladung: {ranged_surplus}W")
        return ranged_surplus

    def _control_range(self, surplus):
        control_range_low = data.data.general_data.data.chargemode_config.pv_charging.control_range[0]
        control_range_high = data.data.general_data.data.chargemode_config.pv_charging.control_range[1]
        control_range_center = control_range_high - \
            (control_range_high - control_range_low) / 2
        if control_range_low < surplus < control_range_high:
            available_power = 0
        else:
            available_power = surplus + control_range_center
        return available_power

    SWITCH_ON_FALLEN_BELOW = "Einschaltschwelle von {}W während der Einschaltverzögerung unterschritten."
    SWITCH_ON_WAITING = "Die Ladung wird gestartet, sobald nach {}s die Einschaltverzögerung abgelaufen ist."
    SWITCH_ON_NOT_EXCEEDED = ("Die Ladung kann nicht gestartet werden, da die Einschaltschwelle {}W nicht erreicht "
                              "wird.")
    SWITCH_ON_EXPIRED = "Einschaltschwelle von {}W für die Dauer der Einschaltverzögerung überschritten."

    def calc_switch_on_power(self, chargepoint: Chargepoint) -> Tuple[float, float]:
        surplus = self.data.set.surplus_power_left - self.data.set.reserved_surplus
        control_parameter = chargepoint.data.set.charging_ev_data.data.control_parameter
        pv_config = data.data.general_data.data.chargemode_config.pv_charging

        if chargepoint.data.set.charging_ev_data.charge_template.data.chargemode.pv_charging.feed_in_limit:
            threshold = pv_config.feed_in_yield
        else:
            threshold = pv_config.switch_on_threshold*control_parameter.phases
        return surplus, threshold

    def switch_on_threshold_reached(self, chargepoint: Chargepoint) -> None:
        try:
            message = None
            control_parameter = chargepoint.data.set.charging_ev_data.data.control_parameter
            feed_in_limit = chargepoint.data.set.charging_ev_data.charge_template.data.chargemode.pv_charging.\
                feed_in_limit
            pv_config = data.data.general_data.data.chargemode_config.pv_charging
            timestamp_switch_on_off = control_parameter.timestamp_switch_on_off

            surplus, threshold = self.calc_switch_on_power(chargepoint)
            power_to_reserve = pv_config.switch_on_threshold*control_parameter.phases
            if control_parameter.state == ChargepointState.SWITCH_ON_DELAY:
                # Wurde die Einschaltschwelle erreicht? Reservierte Leistung aus all_surplus rausrechnen,
                # da diese Leistung ja schon reserviert wurde, als die Einschaltschwelle erreicht wurde.
                if surplus + power_to_reserve <= threshold:
                    # Einschaltschwelle wurde unterschritten, Timer zurücksetzen
                    timestamp_switch_on_off = None
                    self.data.set.reserved_surplus -= power_to_reserve
                    message = self.SWITCH_ON_FALLEN_BELOW.format(pv_config.switch_on_threshold)
                    control_parameter.state = ChargepointState.NO_CHARGING_ALLOWED
            else:
                # Timer starten
                if (surplus >= threshold) and ((feed_in_limit and self.data.set.reserved_surplus == 0) or
                                               not feed_in_limit):
                    timestamp_switch_on_off = timecheck.create_timestamp()
                    self.data.set.reserved_surplus += power_to_reserve
                    message = self.SWITCH_ON_WAITING.format(pv_config.switch_on_delay)
                    control_parameter.state = ChargepointState.SWITCH_ON_DELAY
                else:
                    # Einschaltschwelle nicht erreicht
                    message = self.SWITCH_ON_NOT_EXCEEDED.format(pv_config.switch_on_threshold)

            if timestamp_switch_on_off != control_parameter.timestamp_switch_on_off:
                control_parameter.timestamp_switch_on_off = timestamp_switch_on_off
                Pub().pub(f"openWB/set/vehicle/{chargepoint.data.set.charging_ev_data.num}/control_parameter/"
                          f"timestamp_switch_on_off", timestamp_switch_on_off)
            chargepoint.set_state_and_log(message)
        except Exception:
            log.exception("Fehler im allgemeinen PV-Modul")

    def switch_on_timer_expired(self, chargepoint: Chargepoint) -> None:
        """ prüft, ob die Einschaltschwelle erreicht wurde, reserviert Leistung und gibt diese frei
        bzw. stoppt die Freigabe wenn die Ausschaltschwelle und -verzögerung erreicht wurde.

        Erst wenn für eine bestimmte Zeit eine bestimmte Grenze über/unter-
        schritten wurde, wird die Ladung gestartet/gestoppt. So wird häufiges starten/stoppen
        vermieden. Die Grenzen aus den Einstellungen sind als Deltas zu verstehen, die absoluten
        Schaltpunkte ergeben sich ggf noch aus der Einspeisegrenze.
        """
        try:
            msg = None
            pv_config = data.data.general_data.data.chargemode_config.pv_charging
            control_parameter = chargepoint.data.set.charging_ev_data.data.control_parameter
            # Timer ist noch nicht abgelaufen
            if timecheck.check_timestamp(control_parameter.timestamp_switch_on_off,
                                         pv_config.switch_on_delay):
                msg = self.SWITCH_ON_WAITING.format(pv_config.switch_on_delay)
            # Timer abgelaufen
            else:
                control_parameter.timestamp_switch_on_off = None
                self.data.set.reserved_surplus -= pv_config.switch_on_threshold*control_parameter.phases
                msg = self.SWITCH_ON_EXPIRED.format(pv_config.switch_on_threshold)
                Pub().pub(
                    "openWB/set/vehicle/" + str(chargepoint.data.set.charging_ev_data.num) +
                    "/control_parameter/timestamp_switch_on_off", None)
                control_parameter.state = ChargepointState.CHARGING_ALLOWED
            chargepoint.set_state_and_log(msg)
        except Exception:
            log.exception("Fehler im allgemeinen PV-Modul")

    SWITCH_OFF_STOP = "Ladevorgang nach Ablauf der Abschaltverzögerung gestoppt."
    SWITCH_OFF_WAITING = "Ladevorgang wird nach Ablauf der Abschaltverzögerung {}s gestoppt."
    SWITCH_OFF_NO_STOP = ("Stoppen des Ladevorgangs verhindert, da in der Fahrzeug-Vorlage die Einstellung"
                          " 'Ladung aktiv halten' aktiviert ist.")
    SWITCH_OFF_EXCEEDED = "Abschaltschwelle während der Verzögerung überschritten."
    SWITCH_OFF_NOT_CHARGING = ("Da das EV nicht lädt und die Abschaltschwelle erreicht wird, "
                               "wird die Ladefreigabe sofort entzogen.")

    def switch_off_check_timer(self, chargepoint: Chargepoint) -> None:
        try:
            msg = None
            pv_config = data.data.general_data.data.chargemode_config.pv_charging
            control_parameter = chargepoint.data.set.charging_ev_data.data.control_parameter

            if control_parameter.timestamp_switch_on_off is not None:
                if not timecheck.check_timestamp(
                        control_parameter.timestamp_switch_on_off,
                        pv_config.switch_off_delay):
                    control_parameter.timestamp_switch_on_off = None
                    self.data.set.released_surplus -= chargepoint.data.set.required_power
                    msg = self.SWITCH_OFF_STOP
                    Pub().pub(
                        "openWB/set/vehicle/" + str(chargepoint.data.set.charging_ev_data.num) +
                        "/control_parameter/timestamp_switch_on_off", None)
                    control_parameter.state = ChargepointState.NO_CHARGING_ALLOWED
                else:
                    msg = self.SWITCH_OFF_WAITING.format(pv_config.switch_off_delay)
            chargepoint.set_state_and_log(msg)
        except Exception:
            log.exception("Fehler im allgemeinen PV-Modul")

    def calc_switch_off_threshold(self, chargepoint: Chargepoint) -> Tuple[float, float]:
        pv_config = data.data.general_data.data.chargemode_config.pv_charging
        charging_ev_data = chargepoint.data.set.charging_ev_data
        control_parameter = charging_ev_data.data.control_parameter
        if chargepoint.data.set.charging_ev_data.charge_template.data.chargemode.pv_charging.feed_in_limit:
            # Der EVU-Überschuss muss ggf um die Einspeisegrenze bereinigt werden.
            # Wnn die Leistung nicht Einspeisegrenze + Einschaltschwelle erreicht, darf die Ladung nicht pulsieren.
            # Abschaltschwelle um Einschaltschwelle reduzieren.
            feed_in_yield = (-data.data.general_data.data.chargemode_config.pv_charging.feed_in_yield
                             + pv_config.switch_on_threshold*control_parameter.phases)
        else:
            feed_in_yield = 0
        threshold = pv_config.switch_off_threshold + feed_in_yield
        return threshold, feed_in_yield

    def calc_switch_off(self, chargepoint: Chargepoint) -> Tuple[float, float]:
        switch_off_power = - self.calc_surplus() - self.data.set.released_surplus
        threshold, feed_in_yield = self.calc_switch_off_threshold(chargepoint)
        log.debug(f'LP{chargepoint.num} Switch-Off-Threshold prüfen: {switch_off_power}W, Schwelle: {threshold}W, '
                  f'freigegebener Überschuss {self.data.set.released_surplus}W, Einspeisegrenze {feed_in_yield}W')
        return switch_off_power, threshold

    def switch_off_check_threshold(self, chargepoint: Chargepoint) -> bool:
        """ prüft, ob die Abschaltschwelle erreicht wurde und startet die Abschaltverzögerung.
        Ist die Abschaltverzögerung bereits aktiv, wird geprüft, ob die Abschaltschwelle wieder
        unterschritten wurde, sodass die Verzögerung wieder gestoppt wird.
        """
        charge = True
        msg = None
        charging_ev_data = chargepoint.data.set.charging_ev_data
        control_parameter = charging_ev_data.data.control_parameter
        timestamp_switch_on_off = control_parameter.timestamp_switch_on_off

        power_in_use, threshold = self.calc_switch_off(chargepoint)
        if control_parameter.state == ChargepointState.SWITCH_OFF_DELAY:
            # Wenn automatische Phasenumschaltung aktiv, die Umschaltung abwarten, bevor die Abschaltschwelle
            # greift.
            if control_parameter.state == ChargepointState.PHASE_SWITCH_DELAY:
                timestamp_switch_on_off = None
                self.data.set.released_surplus -= chargepoint.data.set.required_power
                log.info("Abschaltverzögerung gestoppt, da die Verzögerung für die Phasenumschaltung aktiv ist. " +
                         "Diese wird abgewartet, bevor die Abschaltverzögerung gestartet wird.")
            # Wurde die Abschaltschwelle erreicht?
            # Eigene Leistung aus der freigegebenen Leistung rausrechnen.
            if power_in_use + chargepoint.data.set.required_power < threshold:
                timestamp_switch_on_off = None
                self.data.set.released_surplus -= chargepoint.data.set.required_power
                msg = self.SWITCH_OFF_EXCEEDED
                control_parameter.state = ChargepointState.CHARGING_ALLOWED
        else:
            # Wurde die Abschaltschwelle ggf. durch die Verzögerung anderer LP erreicht?
            min_current = (charging_ev_data.ev_template.data.min_current
                           + charging_ev_data.ev_template.data.nominal_difference)
            if power_in_use > threshold and max(chargepoint.data.get.currents) <= min_current:
                if not charging_ev_data.ev_template.data.prevent_charge_stop:
                    # EV, die ohnehin nicht laden, wird direkt die Ladefreigabe entzogen.
                    # Würde man required_power vom released_evu_surplus subtrahieren, würden keine anderen EVs
                    # abgeschaltet werden und nach der Abschaltverzögerung des nicht-ladeden EVs wäre die
                    # Abschaltschwelle immer noch überschritten. Würde man die tatsächliche Leistung von
                    # released_evu_surplus subtrahieren, würde released_evu_surplus nach Ablauf der Verzögerung
                    # nicht 0 sein, wenn sich die Ladeleistung zwischendurch verändert hat.
                    if chargepoint.data.get.charge_state is False:
                        charge = False
                        msg = self.SWITCH_OFF_NOT_CHARGING
                        control_parameter.state = ChargepointState.NO_CHARGING_ALLOWED
                    else:
                        timestamp_switch_on_off = timecheck.create_timestamp()
                        # merken, dass ein LP verzögert wird, damit nicht zu viele LP verzögert werden.
                        self.data.set.released_surplus += chargepoint.data.set.required_power
                        msg = self.SWITCH_OFF_WAITING.format(
                            data.data.general_data.data.chargemode_config.pv_charging.switch_off_delay)
                        control_parameter.state = ChargepointState.SWITCH_OFF_DELAY
                    # Die Abschaltschwelle wird immer noch überschritten und es sollten weitere LP abgeschaltet
                    # werden.
                else:
                    msg = self.SWITCH_OFF_NO_STOP
        if timestamp_switch_on_off != control_parameter.timestamp_switch_on_off:
            control_parameter.timestamp_switch_on_off = timestamp_switch_on_off
            Pub().pub(f"openWB/set/vehicle/{charging_ev_data.num}/control_parameter/"
                      f"timestamp_switch_on_off", timestamp_switch_on_off)
        chargepoint.set_state_and_log(msg)
        return charge

    def reset_switch_on_off(self, chargepoint: Chargepoint, charging_ev: Ev):
        """ Zeitstempel und reservierte Leistung löschen

        Parameter
        ---------
        chargepoint: dict
            Ladepunkt, für den die Werte zurückgesetzt werden sollen
        charging_ev: dict
            EV, das dem Ladepunkt zugeordnet ist
        """
        try:
            if charging_ev.data.control_parameter.timestamp_switch_on_off is not None:
                charging_ev.data.control_parameter.timestamp_switch_on_off = None
                evu_counter = data.data.counter_all_data.get_evu_counter()
                Pub().pub("openWB/set/vehicle/"+str(charging_ev.num) +
                          "/control_parameter/timestamp_switch_on_off", None)
                # Wenn bereits geladen wird, freigegebene Leistung freigeben. Wenn nicht geladen wird, reservierte
                # Leistung freigeben.
                pv_config = data.data.general_data.data.chargemode_config.pv_charging
                if not chargepoint.data.get.charge_state:
                    evu_counter.data.set.reserved_surplus -= (pv_config.switch_on_threshold
                                                              * chargepoint.data.set.phases_to_use)
                else:
                    evu_counter.data.set.released_surplus -= (pv_config.switch_on_threshold
                                                              * charging_ev.data.control_parameter.phases)
        except Exception:
            log.exception("Fehler im allgemeinen PV-Modul")

    def reset_pv_data(self):
        """ setzt die Daten zurück, die über mehrere Regelzyklen genutzt werden.
        """
        try:
            Pub().pub(f"openWB/set/counter/{self.num}/set/reserved_surplus", 0)
            Pub().pub(f"openWB/set/counter/{self.num}/set/released_surplus", 0)
            self.data.set.reserved_surplus = 0
            self.data.set.released_surplus = 0
        except Exception:
            log.exception("Fehler im allgemeinen PV-Modul")


def limit_raw_power_left_to_surplus(surplus) -> None:
    for counter in data.data.counter_data.values():
        # Zwischenzähler werden nur nach Strömen begrenzt, daher kann hier die Leistung vom EVU-Zähler gesetzt werden
        counter.data.set.surplus_power_left = surplus
        log.debug(f'Zähler {counter.num}: Begrenzung der verbleibenden Leistung auf '
                  f'{counter.data.set.surplus_power_left}W')
