""" EV-Logik
ermittelt, den Ladestrom, den das EV gerne zur Verfügung hätte.

In den control Parametern wird sich der Lademodus, Submodus, Priorität, Phasen und Stromstärke gemerkt,
mit denen das EV aktuell in der Regelung berücksichtigt wird. Bei der Ermittlung der benötigten Strom-
stärke wird auch geprüft, ob sich an diesen Parametern etwas geändert hat. Falls ja, muss das EV
in der Regelung neu priorisiert werden und eine neue Zuteilung des Stroms erhalten.
"""
from dataclasses import dataclass, field
import logging
from typing import List, Optional, Tuple

from control import data
from control.chargepoint.chargepoint_state import ChargepointState, PHASE_SWITCH_STATES
from control.chargepoint.charging_type import ChargingType
from control.chargepoint.control_parameter import ControlParameter
from control.ev.charge_template import ChargeTemplate
from control.ev.ev_template import EvTemplate
from control.limiting_value import LimitingValue
from dataclass_utils.factories import empty_list_factory
from helpermodules import timecheck
from helpermodules.constants import NO_ERROR
from modules.common.abstract_vehicle import VehicleUpdateData
from modules.common.configurable_vehicle import ConfigurableVehicle

log = logging.getLogger(__name__)


def get_vehicle_default() -> dict:
    return {
        "charge_template": 0,
        "ev_template": 0,
        "name": "Fahrzeug",
        "info": {
            "manufacturer": None,
            "model": None,
        },
        "tag_id": [],
        "get/soc": 0
    }


@dataclass
class Set:
    soc_error_counter: int = field(
        default=0, metadata={"topic": "set/soc_error_counter"})


def set_factory() -> Set:
    return Set()


@dataclass
class Get:
    soc: Optional[int] = field(default=None, metadata={"topic": "get/soc"})
    soc_request_timestamp: Optional[float] = field(
        default=None, metadata={"topic": "get/soc_request_timestamp"})
    soc_timestamp: Optional[float] = field(
        default=None, metadata={"topic": "get/soc_timestamp"})
    force_soc_update: bool = field(default=False, metadata={
                                   "topic": "get/force_soc_update"})
    range: Optional[float] = field(default=None, metadata={"topic": "get/range"})
    fault_state: int = field(default=0, metadata={"topic": "get/fault_state"})
    fault_str: str = field(default=NO_ERROR, metadata={"topic": "get/fault_str"})


def get_factory() -> Get:
    return Get()


@dataclass
class EvData:
    set: Set = field(default_factory=set_factory)
    charge_template: int = field(default=0, metadata={"topic": "charge_template"})
    ev_template: int = field(default=0, metadata={"topic": "ev_template"})
    name: str = field(default="neues Fahrzeug", metadata={"topic": "name"})
    tag_id: List[str] = field(default_factory=empty_list_factory, metadata={
        "topic": "tag_id"})
    get: Get = field(default_factory=get_factory)


class Ev:
    """Logik des EV
    """

    def __init__(self, index: int):
        try:
            self.ev_template: EvTemplate = EvTemplate()
            self.charge_template: ChargeTemplate = ChargeTemplate(0)
            self.soc_module: ConfigurableVehicle = None
            self.chargemode_changed = False
            self.submode_changed = False
            self.num = index
            self.data = EvData()
        except Exception:
            log.exception("Fehler im ev-Modul "+str(self.num))

    def soc_interval_expired(self, vehicle_update_data: VehicleUpdateData) -> bool:
        request_soc = False
        if self.data.get.soc_request_timestamp is None:
            # Initiale Abfrage
            request_soc = True
        else:
            if vehicle_update_data.plug_state is True or self.soc_module.general_config.request_only_plugged is False:
                if (vehicle_update_data.charge_state is True or
                        (self.data.set.soc_error_counter < 3 and self.data.get.fault_state == 2)):
                    interval = self.soc_module.general_config.request_interval_charging
                else:
                    interval = self.soc_module.general_config.request_interval_not_charging
                # Zeitstempel prüfen, ob wieder abgefragt werden muss.
                if timecheck.check_timestamp(self.data.get.soc_request_timestamp, interval-5) is False:
                    # Zeit ist abgelaufen
                    request_soc = True
        return request_soc

    def get_required_current(self,
                             control_parameter: ControlParameter,
                             imported: float,
                             max_phases_hw: int,
                             phase_switch_supported: bool,
                             charging_type: str) -> Tuple[bool, Optional[str], str, float, int]:
        """ ermittelt, ob und mit welchem Strom das EV geladen werden soll (unabhängig vom Lastmanagement)

        Parameter
        ---------
        imported_since_mode_switch: float
            seit dem letzten Lademodi-Wechsel geladene Energie.
        Return
        ------
        state: bool
            Soll geladen werden?
        message: str
            Nachricht, warum nicht geladen werden soll
        submode: str
            Lademodus, in dem tatsächlich geladen wird
        required_current: int
            Strom, der nach Ladekonfiguration benötigt wird
        """
        phases = None
        required_current = None
        submode = None
        message = None
        state = True
        try:
            if self.charge_template.data.chargemode.selected == "scheduled_charging":
                if control_parameter.imported_at_plan_start is None:
                    control_parameter.imported_at_plan_start = imported
                used_amount = imported - control_parameter.imported_at_plan_start
                plan_data = self.charge_template.scheduled_charging_recent_plan(
                    self.data.get.soc,
                    self.ev_template,
                    control_parameter.phases,
                    used_amount,
                    max_phases_hw,
                    phase_switch_supported,
                    charging_type)
                soc_request_interval_offset = 0
                if plan_data:
                    # Wenn mit einem neuen Plan geladen wird, muss auch die Energiemenge von neuem gezählt werden.
                    if (self.charge_template.data.chargemode.scheduled_charging.plans[str(plan_data.id)].limit.
                            selected == "amount" and
                            plan_data.id != control_parameter.current_plan):
                        control_parameter.imported_at_plan_start = imported
                    # Wenn der SoC ein paar Minuten alt ist, kann der Termin trotzdem gehalten werden.
                    # Zielladen kann nicht genauer arbeiten, als das Abfrageintervall vom SoC.
                    if (self.soc_module and
                            self.charge_template.data.chargemode.
                            scheduled_charging.plans[str(plan_data.id)].limit.selected == "soc"):
                        soc_request_interval_offset = self.soc_module.general_config.request_interval_charging
                    control_parameter.current_plan = plan_data.id
                else:
                    control_parameter.current_plan = None
                required_current, submode, message, phases = self.charge_template.scheduled_charging_calc_current(
                    plan_data,
                    self.data.get.soc,
                    used_amount,
                    control_parameter.phases,
                    control_parameter.min_current,
                    soc_request_interval_offset)

            # Wenn Zielladen auf Überschuss wartet, prüfen, ob Zeitladen aktiv ist.
            if (submode != "instant_charging" and
                    self.charge_template.data.time_charging.active):
                if control_parameter.imported_at_plan_start is None:
                    control_parameter.imported_at_plan_start = imported
                used_amount = imported - control_parameter.imported_at_plan_start
                tmp_current, tmp_submode, tmp_message, plan_id = self.charge_template.time_charging(
                    self.data.get.soc,
                    used_amount,
                    charging_type
                )
                # Info vom Zielladen erhalten
                message = f"{message or ''} {tmp_message or ''}".strip()
                if tmp_current > 0:
                    # Wenn mit einem neuen Plan geladen wird, muss auch die Energiemenge von neuem gezählt werden.
                    if plan_id != control_parameter.current_plan:
                        control_parameter.imported_at_plan_start = imported
                    control_parameter.current_plan = plan_id
                    required_current = tmp_current
                    submode = tmp_submode
            if (required_current == 0) or (required_current is None):
                if self.charge_template.data.chargemode.selected == "instant_charging":
                    # Wenn der Submode auf stop gestellt wird, wird auch die Energiemenge seit Wechsel des Modus
                    # zurückgesetzt, dann darf nicht die Energiemenge erneute geladen werden.
                    if control_parameter.imported_instant_charging is None:
                        control_parameter.imported_instant_charging = imported
                    used_amount = imported - control_parameter.imported_instant_charging
                    required_current, submode, message = self.charge_template.instant_charging(
                        self.data.get.soc,
                        used_amount,
                        charging_type)
                elif self.charge_template.data.chargemode.selected == "pv_charging":
                    required_current, submode, message = self.charge_template.pv_charging(
                        self.data.get.soc, control_parameter.min_current, charging_type)
                elif self.charge_template.data.chargemode.selected == "standby":
                    # Text von Zeit-und Zielladen nicht überschreiben.
                    if message is None:
                        required_current, submode, message = self.charge_template.standby()
                    else:
                        required_current, submode, _ = self.charge_template.standby()
                elif self.charge_template.data.chargemode.selected == "stop":
                    required_current, submode, message = self.charge_template.stop()
            if submode == "stop" or submode == "standby" or (self.charge_template.data.chargemode.selected == "stop"):
                state = False
            if phases is None:
                phases = control_parameter.phases
            return state, message, submode, required_current, phases
        except Exception as e:
            log.exception("Fehler im ev-Modul "+str(self.num))
            return (False, f"Kein Ladevorgang, da ein Fehler aufgetreten ist: {' '.join(e.args)}", "stop", 0,
                    control_parameter.phases)

    def set_chargemode_changed(self, control_parameter: ControlParameter, submode: str) -> None:
        if ((submode == "time_charging" and control_parameter.chargemode != "time_charging") or
                (submode != "time_charging" and
                 control_parameter.chargemode != self.charge_template.data.chargemode.selected)):
            self.chargemode_changed = True
            log.debug("Änderung des Lademodus")
        else:
            self.chargemode_changed = False

    def set_submode_changed(self, control_parameter: ControlParameter, submode: str) -> None:
        self.submode_changed = (submode != control_parameter.submode)

    def check_min_max_current(self,
                              control_parameter: ControlParameter,
                              required_current: float,
                              phases: int,
                              charging_type: str,
                              pv: bool = False,) -> Tuple[float, Optional[str]]:
        """ prüft, ob der gesetzte Ladestrom über dem Mindest-Ladestrom und unter dem Maximal-Ladestrom des EVs liegt.
        Falls nicht, wird der Ladestrom auf den Mindest-Ladestrom bzw. den Maximal-Ladestrom des EV gesetzt.
        Wenn PV-Laden aktiv ist, darf die Stromstärke nicht unter den PV-Mindeststrom gesetzt werden.
        """
        msg = None
        # Überprüfung bei 0 (automatische Umschaltung) erfolgt nach der Prüfung der Phasenumschaltung, wenn fest
        # steht, mit vielen Phasen geladen werden soll.
        if phases != 0:
            # EV soll/darf nicht laden
            if required_current != 0:
                if not pv:
                    if charging_type == ChargingType.AC.value:
                        min_current = self.ev_template.data.min_current
                    else:
                        min_current = self.ev_template.data.dc_min_current
                else:
                    min_current = control_parameter.required_current
                if required_current < min_current:
                    required_current = min_current
                    msg = ("Die Einstellungen in dem Fahrzeug-Profil beschränken den Strom auf "
                           f"mindestens {required_current} A.")
                else:
                    if charging_type == ChargingType.AC.value:
                        if phases == 1:
                            max_current = self.ev_template.data.max_current_single_phase
                        else:
                            max_current = self.ev_template.data.max_current_multi_phases
                    else:
                        max_current = self.ev_template.data.dc_max_current
                    if required_current > max_current:
                        required_current = max_current
                        msg = ("Die Einstellungen in dem Fahrzeug-Profil beschränken den Strom auf "
                               f"maximal {required_current} A.")
        return required_current, msg

    CURRENT_OUT_OF_NOMINAL_DIFFERENCE = (", da das Fahrzeug nicht mit der vorgegebenen Stromstärke +/- der erlaubten "
                                         + "Stromabweichung aus dem Fahrzeug-Profil/Minimalen Dauerstrom lädt.")
    ENOUGH_POWER = ", da ausreichend Überschuss für mehrphasiges Laden zur Verfügung steht."
    NOT_ENOUGH_POWER = ", da nicht ausreichend Überschuss für mehrphasiges Laden zur Verfügung steht."

    def _check_phase_switch_conditions(self,
                                       control_parameter: ControlParameter,
                                       get_currents: List[float],
                                       get_power: float,
                                       max_current_cp: int,
                                       limit: LimitingValue) -> Tuple[bool, Optional[str]]:
        # Manche EV laden mit 6.1A bei 6A Soll-Strom
        min_current = (max(control_parameter.min_current, control_parameter.required_current) +
                       self.ev_template.data.nominal_difference)
        max_current = (min(self.ev_template.data.max_current_single_phase, max_current_cp)
                       - self.ev_template.data.nominal_difference)
        phases_in_use = control_parameter.phases
        pv_config = data.data.general_data.data.chargemode_config.pv_charging
        max_phases_ev = self.ev_template.data.max_phases
        if self.charge_template.data.chargemode.pv_charging.feed_in_limit:
            feed_in_yield = pv_config.feed_in_yield
        else:
            feed_in_yield = 0
        all_surplus = data.data.counter_all_data.get_evu_counter().get_usable_surplus(feed_in_yield)
        required_surplus = control_parameter.min_current * max_phases_ev * 230 - get_power
        condition_1_to_3 = (((max(get_currents) > max_current and
                            all_surplus > required_surplus) or limit == LimitingValue.UNBALANCED_LOAD.value) and
                            phases_in_use == 1)
        condition_3_to_1 = max(get_currents) < min_current and all_surplus <= 0 and phases_in_use > 1
        if condition_1_to_3 or condition_3_to_1:
            return True, None
        else:
            if phases_in_use > 1 and all_surplus > 0:
                return False, self.ENOUGH_POWER
            elif phases_in_use == 1 and all_surplus < required_surplus:
                return False, self.NOT_ENOUGH_POWER
            else:
                return False, self.CURRENT_OUT_OF_NOMINAL_DIFFERENCE

    PHASE_SWITCH_DELAY_TEXT = '{} Phasen in {}.'

    def auto_phase_switch(self,
                          control_parameter: ControlParameter,
                          cp_num: int,
                          get_currents: List[float],
                          get_power: float,
                          max_current_cp: int,
                          max_phases: int,
                          limit: LimitingValue) -> Tuple[int, float, Optional[str]]:
        message = None
        timestamp_last_phase_switch = control_parameter.timestamp_last_phase_switch
        current = control_parameter.required_current
        phases_to_use = control_parameter.phases
        phases_in_use = control_parameter.phases
        pv_config = data.data.general_data.data.chargemode_config.pv_charging
        cm_config = data.data.general_data.data.chargemode_config
        if self.charge_template.data.chargemode.pv_charging.feed_in_limit:
            feed_in_yield = pv_config.feed_in_yield
        else:
            feed_in_yield = 0
        all_surplus = data.data.counter_all_data.get_evu_counter().get_usable_surplus(feed_in_yield)
        delay = cm_config.phase_switch_delay * 60
        if phases_in_use == 1:
            direction_str = f"Umschaltung von 1 auf {max_phases}"
            required_reserved_power = (control_parameter.min_current * max_phases * 230 -
                                       self.ev_template.data.max_current_single_phase * 230)

            new_phase = max_phases
            new_current = control_parameter.min_current
        else:
            direction_str = f"Umschaltung von {max_phases} auf 1"
            # Es kann einphasig mit entsprechend niedriger Leistung gestartet werden.
            required_reserved_power = 0
            new_phase = 1
            new_current = self.ev_template.data.max_current_single_phase

        log.debug(
            f'Genutzter Strom: {max(get_currents)}A, Überschuss: {all_surplus}W, benötigte neue Leistung: '
            f'{required_reserved_power}W')
        # Wenn gerade umgeschaltet wird, darf kein Timer gestartet werden.
        if not self.ev_template.data.prevent_phase_switch:
            condition, condition_msg = self._check_phase_switch_conditions(control_parameter,
                                                                           get_currents,
                                                                           get_power,
                                                                           max_current_cp,
                                                                           limit)
            if control_parameter.state not in PHASE_SWITCH_STATES:
                if condition:
                    # Wenn nach der Umschaltung weniger Leistung benötigt wird, soll während der Verzögerung keine
                    # neuen eingeschaltet werden.
                    data.data.counter_all_data.get_evu_counter(
                    ).data.set.reserved_surplus += max(0, required_reserved_power)
                    message = self.PHASE_SWITCH_DELAY_TEXT.format(
                        direction_str,
                        timecheck.convert_timestamp_delta_to_time_string(timestamp_last_phase_switch, delay))
                    control_parameter.state = ChargepointState.PHASE_SWITCH_DELAY
                elif condition_msg:
                    log.debug(f"Keine Phasenumschaltung{condition_msg}")
            else:
                if condition:
                    # Timer laufen lassen
                    if timecheck.check_timestamp(control_parameter.timestamp_last_phase_switch, delay):
                        message = self.PHASE_SWITCH_DELAY_TEXT.format(
                            direction_str,
                            timecheck.convert_timestamp_delta_to_time_string(timestamp_last_phase_switch, delay))
                    else:
                        data.data.counter_all_data.get_evu_counter(
                        ).data.set.reserved_surplus -= max(0, required_reserved_power)
                        phases_to_use = new_phase
                        current = new_current
                        log.debug("Phasenumschaltung kann nun durchgeführt werden.")
                        control_parameter.state = ChargepointState.PHASE_SWITCH_AWAITED
                else:
                    data.data.counter_all_data.get_evu_counter(
                    ).data.set.reserved_surplus -= max(0, required_reserved_power)
                    message = f"Verzögerung für die {direction_str} Phasen abgebrochen{condition_msg}"
                    control_parameter.state = ChargepointState.CHARGING_ALLOWED

        if message:
            log.info(f"LP {cp_num}: {message}")
        return phases_to_use, current, message

    def reset_phase_switch(self, control_parameter: ControlParameter):
        """ Zurücksetzen der Zeitstempel und reservierten Leistung.

        Die Phasenumschaltung kann nicht abgebrochen werden!
        """
        if control_parameter.state == ChargepointState.PHASE_SWITCH_DELAY:
            # Wenn der Timer läuft, ist den Control-Parametern die alte Phasenzahl hinterlegt.
            if control_parameter.phases == 1:
                reserved = control_parameter.required_current * \
                    3 * 230 - self.ev_template.data.max_current_single_phase * 230
                data.data.counter_all_data.get_evu_counter().data.set.reserved_surplus -= reserved
                log.debug(
                    "Zurücksetzen der reservierten Leistung für die Phasenumschaltung. reservierte Leistung: " +
                    str(data.data.counter_all_data.get_evu_counter().data.set.reserved_surplus))
            else:
                reserved = self.ev_template.data.max_current_single_phase * \
                    230 - control_parameter.required_current * 3 * 230
                data.data.counter_all_data.get_evu_counter().data.set.reserved_surplus -= reserved
                log.debug(
                    "Zurücksetzen der reservierten Leistung für die Phasenumschaltung. reservierte Leistung: " +
                    str(data.data.counter_all_data.get_evu_counter().data.set.reserved_surplus))


def get_ev_to_rfid(rfid: str, vehicle_id: Optional[str] = None) -> Optional[int]:
    """ ermittelt zum übergebenen ID-Tag das Fahrzeug

    Parameter
    ---------
    rfid: string
        ID-Tag
    vehicle_id: string
        MAC-Adresse des ID-Tags (nur openWB Pro)

    Return
    ------
    vehicle: int
        Nummer des EV, das zum Tag gehört
    """
    for vehicle in data.data.ev_data:
        try:
            if "ev" in vehicle:
                if vehicle_id is not None and vehicle_id in data.data.ev_data[vehicle].data.tag_id:
                    log.debug(f"MAC {vehicle_id} wird EV {data.data.ev_data[vehicle].num} zugeordnet.")
                    return data.data.ev_data[vehicle].num
                if rfid in data.data.ev_data[vehicle].data.tag_id:
                    log.debug(f"RFID {rfid} wird EV {data.data.ev_data[vehicle].num} zugeordnet.")
                    return data.data.ev_data[vehicle].num
        except Exception:
            log.exception("Fehler im ev-Modul "+vehicle)
            return None
    else:
        return None
