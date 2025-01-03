from dataclasses import asdict, dataclass, field
import logging
import traceback
from typing import Dict, Optional, Tuple

from control import data
from control.chargepoint.charging_type import ChargingType
from control.ev.ev_template import EvTemplate
from dataclass_utils.factories import empty_dict_factory
from helpermodules.abstract_plans import Limit, limit_factory, ScheduledChargingPlan, TimeChargingPlan
from helpermodules import timecheck
log = logging.getLogger(__name__)


def get_new_charge_template() -> dict:
    ct_default = asdict(ChargeTemplateData())
    ct_default["chargemode"]["scheduled_charging"].pop("plans")
    ct_default["time_charging"].pop("plans")
    return ct_default


def get_charge_template_default() -> dict:
    ct_default = asdict(ChargeTemplateData(name="Standard-Lade-Profil"))
    ct_default["chargemode"]["scheduled_charging"].pop("plans")
    ct_default["time_charging"].pop("plans")
    return ct_default


@dataclass
class ScheduledCharging:
    plans: Dict[int, ScheduledChargingPlan] = field(default_factory=empty_dict_factory, metadata={
                                                    "topic": ""})


@dataclass
class TimeCharging:
    active: bool = False
    plans: Dict[int, TimeChargingPlan] = field(default_factory=empty_dict_factory, metadata={
                                               "topic": ""})


@dataclass
class InstantCharging:
    current: int = 10
    dc_current: float = 145
    limit: Limit = field(default_factory=limit_factory)


@dataclass
class PvCharging:
    dc_min_current: float = 145
    dc_min_soc_current: float = 145
    min_soc_current: int = 10
    min_current: int = 0
    feed_in_limit: bool = False
    min_soc: int = 0
    max_soc: int = 100


def pv_charging_factory() -> PvCharging:
    return PvCharging()


def scheduled_charging_factory() -> ScheduledCharging:
    return ScheduledCharging()


def instant_charging_factory() -> InstantCharging:
    return InstantCharging()


@dataclass
class Chargemode:
    selected: str = "stop"
    pv_charging: PvCharging = field(default_factory=pv_charging_factory)
    scheduled_charging: ScheduledCharging = field(default_factory=scheduled_charging_factory)
    instant_charging: InstantCharging = field(default_factory=instant_charging_factory)


def time_charging_factory() -> TimeCharging:
    return TimeCharging()


def chargemode_factory() -> Chargemode:
    return Chargemode()


@dataclass
class Et:
    active: bool = False
    max_price: float = 0.0002


def et_factory() -> Et:
    return Et()


@dataclass
class ChargeTemplateData:
    name: str = "Lade-Profil"
    prio: bool = False
    load_default: bool = False
    et: Et = field(default_factory=et_factory)
    time_charging: TimeCharging = field(default_factory=time_charging_factory)
    chargemode: Chargemode = field(default_factory=chargemode_factory)


def charge_template_data_factory() -> ChargeTemplateData:
    return ChargeTemplateData()


@dataclass
class SelectedPlan:
    remaining_time: float = 0
    available_current: float = 14
    duration: float = 0
    max_current: int = 16
    missing_amount: float = 0
    phases: int = 1
    id: int = 0


@dataclass
class ChargeTemplate:
    """ Klasse der Lade-Profile
    """
    ct_num: int
    data: ChargeTemplateData = field(default_factory=charge_template_data_factory, metadata={
        "topic": ""})

    BUFFER = -1200  # nach mehr als 20 Min Überschreitung wird der Termin als verpasst angesehen
    CHARGING_PRICE_EXCEEDED = "Keine Ladung, da der aktuelle Strompreis über dem maximalen Strompreis liegt."

    TIME_CHARGING_NO_PLAN_CONFIGURED = "Keine Ladung, da keine Zeitfenster für Zeitladen konfiguriert sind."
    TIME_CHARGING_NO_PLAN_ACTIVE = "Keine Ladung, da kein Zeitfenster für Zeitladen aktiv ist."
    TIME_CHARGING_SOC_REACHED = "Kein Zeitladen, da der Soc bereits erreicht wurde."
    TIME_CHARGING_AMOUNT_REACHED = "Kein Zeitladen, da die Energiemenge bereits geladen wurde."

    def time_charging(self,
                      soc: Optional[float],
                      used_amount_time_charging: float,
                      charging_type: str) -> Tuple[int, str, Optional[str], Optional[str]]:
        """ prüft, ob ein Zeitfenster aktiv ist und setzt entsprechend den Ladestrom
        """
        message = None
        try:
            if self.data.time_charging.plans:
                plan = timecheck.check_plans_timeframe(self.data.time_charging.plans)
                if plan is not None:
                    current = plan.current if charging_type == ChargingType.AC.value else plan.dc_current
                    if self.data.et.active and data.data.optional_data.et_provider_available():
                        if not data.data.optional_data.et_price_lower_than_limit(self.data.et.max_price):
                            return 0, "stop", self.CHARGING_PRICE_EXCEEDED, plan.id
                    if plan.limit.selected == "none":  # kein Limit konfiguriert, mit konfigurierter Stromstärke laden
                        return current, "time_charging", message, plan.id
                    elif plan.limit.selected == "soc":  # SoC Limit konfiguriert
                        if soc:
                            if soc < plan.limit.soc:
                                return current, "time_charging", message, plan.id  # Limit nicht erreicht
                            else:
                                return 0, "stop", self.TIME_CHARGING_SOC_REACHED, plan.id  # Limit erreicht
                        else:
                            return plan.current, "time_charging", message, plan.id
                    elif plan.limit.selected == "amount":  # Energiemengenlimit konfiguriert
                        if used_amount_time_charging < plan.limit.amount:
                            return current, "time_charging", message, plan.id  # Limit nicht erreicht
                        else:
                            return 0, "stop", self.TIME_CHARGING_AMOUNT_REACHED, plan.id  # Limit erreicht
                    else:
                        raise TypeError(f'{plan.limit.selected} unbekanntes Zeitladen-Limit.')
                else:
                    message = self.TIME_CHARGING_NO_PLAN_ACTIVE
            else:
                message = self.TIME_CHARGING_NO_PLAN_CONFIGURED
            log.debug(message)
            return 0, "stop", message, None
        except Exception:
            log.exception("Fehler im ev-Modul "+str(self.ct_num))
            return 0, "stop", "Keine Ladung, da da ein interner Fehler aufgetreten ist: "+traceback.format_exc(), None

    INSTANT_CHARGING_SOC_REACHED = "Kein Sofortladen, da der Soc bereits erreicht wurde."
    INSTANT_CHARGING_AMOUNT_REACHED = "Kein Sofortladen, da die Energiemenge bereits geladen wurde."

    def instant_charging(self,
                         soc: Optional[float],
                         imported_instant_charging: float,
                         charging_type: str) -> Tuple[int, str, Optional[str]]:
        """ prüft, ob die Lademengenbegrenzung erreicht wurde und setzt entsprechend den Ladestrom.
        """
        message = None
        try:
            instant_charging = self.data.chargemode.instant_charging
            if charging_type == ChargingType.AC.value:
                current = instant_charging.current
            else:
                current = instant_charging.dc_current
            if self.data.et.active and data.data.optional_data.et_provider_available():
                if not data.data.optional_data.et_price_lower_than_limit(self.data.et.max_price):
                    return 0, "stop", self.CHARGING_PRICE_EXCEEDED
            if instant_charging.limit.selected == "none":
                return current, "instant_charging", message
            elif instant_charging.limit.selected == "soc":
                if soc:
                    if soc < instant_charging.limit.soc:
                        return current, "instant_charging", message
                    else:
                        return 0, "stop", self.INSTANT_CHARGING_SOC_REACHED
                else:
                    return current, "instant_charging", message
            elif instant_charging.limit.selected == "amount":
                if imported_instant_charging < self.data.chargemode.instant_charging.limit.amount:
                    return current, "instant_charging", message
                else:
                    return 0, "stop", self.INSTANT_CHARGING_AMOUNT_REACHED
            else:
                raise TypeError(f'{instant_charging.limit.selected} unbekanntes Sofortladen-Limit.')
        except Exception:
            log.exception("Fehler im ev-Modul "+str(self.ct_num))
            return 0, "stop", "Keine Ladung, da da ein interner Fehler aufgetreten ist: "+traceback.format_exc()

    PV_CHARGING_SOC_REACHED = "Keine Ladung, da der maximale Soc bereits erreicht wurde."
    PV_CHARGING_SOC_CHARGING = ("Ladung evtl. auch ohne PV-Überschuss, da der Mindest-SoC des Fahrzeugs noch nicht "
                                "erreicht wurde.")
    PV_CHARGING_MIN_CURRENT_CHARGING = "Ladung evtl. auch ohne PV-Überschuss, da minimaler Dauerstrom aktiv ist."

    def pv_charging(self, soc: Optional[float], min_current: int, charging_type: str) -> Tuple[int, str, Optional[str]]:
        """ prüft, ob Min-oder Max-Soc erreicht wurden und setzt entsprechend den Ladestrom.
        """
        message = None
        try:
            pv_charging = self.data.chargemode.pv_charging
            if soc is None or soc < pv_charging.max_soc:
                if pv_charging.min_soc != 0 and soc is not None:
                    if soc < pv_charging.min_soc:
                        if charging_type == ChargingType.AC.value:
                            current = pv_charging.min_soc_current
                        else:
                            current = pv_charging.dc_min_soc_current
                        return current, "instant_charging", self.PV_CHARGING_SOC_CHARGING
                if charging_type == ChargingType.AC.value:
                    pv_min_current = pv_charging.min_current
                else:
                    pv_min_current = pv_charging.dc_min_current
                if pv_min_current == 0:
                    # nur PV; Ampere darf nicht 0 sein, wenn geladen werden soll
                    return min_current, "pv_charging", message
                else:
                    # Min PV
                    return pv_min_current, "instant_charging", self.PV_CHARGING_MIN_CURRENT_CHARGING
            else:
                return 0, "stop", self.PV_CHARGING_SOC_REACHED
        except Exception:
            log.exception("Fehler im ev-Modul "+str(self.ct_num))
            return 0, "stop", "Keine Ladung, da ein interner Fehler aufgetreten ist: "+traceback.format_exc()

    def scheduled_charging_recent_plan(self,
                                       soc: float,
                                       ev_template: EvTemplate,
                                       phases: int,
                                       used_amount: float,
                                       max_phases: int,
                                       phase_switch_supported: bool,
                                       charging_type: str) -> Optional[SelectedPlan]:
        """ prüft, ob der Ziel-SoC oder die Ziel-Energiemenge erreicht wurde und stellt den zur Erreichung nötigen
        Ladestrom ein. Um etwas mehr Puffer zu haben, wird bis 20 Min nach dem Zieltermin noch geladen, wenn dieser
        nicht eingehalten werden konnte.
        """
        if phase_switch_supported:
            if charging_type == ChargingType.AC.value:
                max_current = ev_template.data.max_current_multi_phases
            else:
                max_current = ev_template.data.dc_max_current
            instant_phases = data.data.general_data.get_phases_chargemode("scheduled_charging", "instant_charging")
            if instant_phases == 0:
                planned_phases = 3
            else:
                planned_phases = instant_phases
            planned_phases = min(planned_phases, max_phases)
            plan_data = self._search_plan(max_current, soc, ev_template, planned_phases, used_amount, charging_type)
            if (plan_data and
                charging_type == ChargingType.AC.value and
                instant_phases == 0 and
                plan_data.remaining_time > 300 and
                    self.data.et.active is False):
                max_current = ev_template.data.max_current_single_phase
                plan_data_single_phase = self._search_plan(
                    max_current, soc, ev_template, 1, used_amount, charging_type)
                if plan_data_single_phase:
                    if plan_data_single_phase.remaining_time > 0:
                        plan_data = plan_data_single_phase
        else:
            if charging_type == ChargingType.AC.value:
                if phases == 1:
                    max_current = ev_template.data.max_current_single_phase
                else:
                    max_current = ev_template.data.max_current_multi_phases
            else:
                max_current = ev_template.data.dc_max_current
            plan_data = self._search_plan(max_current, soc, ev_template, phases, used_amount, charging_type)
        return plan_data

    def _search_plan(self,
                     max_current: int,
                     soc: Optional[float],
                     ev_template: EvTemplate,
                     phases: int,
                     used_amount: float,
                     charging_type: str) -> Optional[SelectedPlan]:
        smallest_remaining_time = float("inf")
        missed_date_today_of_plan_with_smallest_remaining_time = False
        plan_data: Optional[SelectedPlan] = None
        battery_capacity = ev_template.data.battery_capacity
        for plan in self.data.chargemode.scheduled_charging.plans.values():
            if plan.active:
                if plan.limit.selected == "soc" and soc is None:
                    raise ValueError("Um Zielladen mit SoC-Ziel nutzen zu können, bitte ein SoC-Modul konfigurieren "
                                     f"oder im Plan {plan.name} als Begrenzung Energie einstellen.")
                try:
                    duration, missing_amount = self._calculate_duration(
                        plan, soc, battery_capacity, used_amount, phases, charging_type, ev_template)
                    remaining_time, missed_date_today = timecheck.check_duration(plan, duration, self.BUFFER)
                    if remaining_time:
                        # Wenn der Zeitpunkt vorüber, aber noch nicht abgelaufen ist oder
                        # wenn noch gar kein Plan vorhanden ist,
                        if ((remaining_time < 0 and missed_date_today is False) or
                                # oder der Zeitpunkt noch nicht vorüber ist
                                remaining_time > 0):
                            # Wenn die verbleibende Zeit geringer als die niedrigste bisherige verbleibende Zeit ist
                            if (remaining_time < smallest_remaining_time or
                                    # oder wenn der Zeitpunkt abgelaufen ist und es noch einen Zeitpunkt gibt, der in
                                    # der Zukunft liegt.
                                    (missed_date_today_of_plan_with_smallest_remaining_time and 0 < remaining_time)):
                                smallest_remaining_time = remaining_time
                                missed_date_today_of_plan_with_smallest_remaining_time = missed_date_today
                                if charging_type == ChargingType.AC.value:
                                    available_current = plan.current
                                else:
                                    available_current = plan.dc_current
                                plan_data = SelectedPlan(
                                    remaining_time=remaining_time,
                                    available_current=available_current,
                                    max_current=max_current,
                                    phases=phases,
                                    id=plan.id,
                                    missing_amount=missing_amount,
                                    duration=duration)
                    log.debug(f"Plan-Nr. {plan.id}: Differenz zum Start {remaining_time}s, Dauer {duration/3600}h, "
                              f"Termin heute verpasst: {missed_date_today}")
                except Exception:
                    log.exception("Fehler im ev-Modul "+str(self.ct_num))
        return plan_data

    def _calculate_duration(self,
                            plan: ScheduledChargingPlan,
                            soc: Optional[float],
                            battery_capacity: float,
                            used_amount: float,
                            phases: int,
                            charging_type: str,
                            ev_template: EvTemplate) -> Tuple[float, float]:
        if plan.limit.selected == "soc":
            if soc is not None:
                missing_amount = ((plan.limit.soc_scheduled - soc) / 100) * battery_capacity
            else:
                raise ValueError("Um Zielladen mit SoC-Ziel nutzen zu können, bitte ein SoC-Modul konfigurieren.")
        else:
            missing_amount = plan.limit.amount - used_amount
        current = plan.current if charging_type == ChargingType.AC.value else plan.dc_current
        current = max(current, ev_template.data.min_current if charging_type ==
                      ChargingType.AC.value else ev_template.data.dc_min_current)
        duration = missing_amount/(current * phases*230) * 3600
        return duration, missing_amount

    SCHEDULED_REACHED_LIMIT_SOC = ("Kein Zielladen, da noch Zeit bis zum Zieltermin ist. "
                                   "Kein Zielladen mit Überschuss, da das SoC-Limit für Überschuss-Laden " +
                                   "erreicht wurde.")
    SCHEDULED_CHARGING_REACHED_LIMIT_SOC = ("Kein Zielladen, da das Limit für Fahrzeug Laden mit Überschuss (SoC-Limit)"
                                            " sowie der Fahrzeug-SoC (Ziel-SoC) bereits erreicht wurde.")
    SCHEDULED_CHARGING_REACHED_AMOUNT = "Kein Zielladen, da die Energiemenge bereits erreicht wurde."
    SCHEDULED_CHARGING_REACHED_SCHEDULED_SOC = ("Falls vorhanden wird mit EVU-Überschuss geladen, da der Ziel-Soc "
                                                "für Zielladen bereits erreicht wurde.")
    SCHEDULED_CHARGING_NO_PLANS_CONFIGURED = "Keine Ladung, da keine Ziel-Termine konfiguriert sind."
    SCHEDULED_CHARGING_NO_DATE_PENDING = "Kein Zielladen, da kein Ziel-Termin ansteht."
    SCHEDULED_CHARGING_USE_PV = ("Kein Zielladen, da noch Zeit bis zum Zieltermin ist. Falls vorhanden, "
                                 "wird mit Überschuss geladen.")
    SCHEDULED_CHARGING_MAX_CURRENT = ("Zielladen mit {}A. Der Ladestrom wurde erhöht, um den Zieltermin zu erreichen. "
                                      "Es wird bis max. 20 Minuten nach dem angegebenen Zieltermin geladen.")
    SCHEDULED_CHARGING_LIMITED_BY_SOC = 'einen SoC von {}%'
    SCHEDULED_CHARGING_LIMITED_BY_AMOUNT = '{}kWh geladene Energie'
    SCHEDULED_CHARGING_IN_TIME = ('Zielladen mit mindestens {}A, um {} um {} zu erreichen. Falls vorhanden wird '
                                  'zusätzlich EVU-Überschuss geladen.')
    SCHEDULED_CHARGING_CHEAP_HOUR = "Zielladen, da ein günstiger Zeitpunkt zum preisbasierten Laden ist."
    SCHEDULED_CHARGING_EXPENSIVE_HOUR = ("Zielladen ausstehend, da jetzt kein günstiger Zeitpunkt zum preisbasierten "
                                         "Laden ist. Falls vorhanden, wird mit Überschuss geladen.")

    def scheduled_charging_calc_current(self,
                                        plan_data: Optional[SelectedPlan],
                                        soc: int,
                                        used_amount: float,
                                        control_parameter_phases: int,
                                        min_current: int,
                                        soc_request_interval_offset: int) -> Tuple[float, str, str, int]:
        current = 0
        submode = "stop"
        if plan_data is None:
            if len(self.data.chargemode.scheduled_charging.plans) == 0:
                return current, submode, self.SCHEDULED_CHARGING_NO_PLANS_CONFIGURED, control_parameter_phases
            else:
                return current, submode, self.SCHEDULED_CHARGING_NO_DATE_PENDING, control_parameter_phases
        current_plan = self.data.chargemode.scheduled_charging.plans[str(plan_data.id)]
        limit = current_plan.limit
        phases = plan_data.phases
        log.debug("Verwendeter Plan: "+str(current_plan.name))
        if limit.selected == "soc" and soc >= limit.soc_limit and soc >= limit.soc_scheduled:
            message = self.SCHEDULED_CHARGING_REACHED_LIMIT_SOC
        elif limit.selected == "soc" and limit.soc_scheduled <= soc < limit.soc_limit:
            message = self.SCHEDULED_CHARGING_REACHED_SCHEDULED_SOC
            current = min_current
            submode = "pv_charging"
            # bei Überschuss-Laden mit der Phasenzahl aus den control_parameter laden,
            # um die Umschaltung zu berücksichtigen.
            phases = control_parameter_phases
        elif limit.selected == "amount" and used_amount >= limit.amount:
            message = self.SCHEDULED_CHARGING_REACHED_AMOUNT
        elif 0 - soc_request_interval_offset < plan_data.remaining_time < 300 + soc_request_interval_offset:
            # 5 Min vor spätestem Ladestart
            if limit.selected == "soc":
                limit_string = self.SCHEDULED_CHARGING_LIMITED_BY_SOC.format(limit.soc_scheduled)
            else:
                limit_string = self.SCHEDULED_CHARGING_LIMITED_BY_AMOUNT.format(limit.amount/1000)
            message = self.SCHEDULED_CHARGING_IN_TIME.format(
                plan_data.available_current, limit_string, current_plan.time)
            current = plan_data.available_current
            submode = "instant_charging"
        # weniger als die berechnete Zeit verfügbar
        # Ladestart wurde um maximal 20 Min verpasst.
        elif plan_data.remaining_time <= 0 - soc_request_interval_offset:
            if plan_data.duration + plan_data.remaining_time < 0:
                current = plan_data.max_current
            else:
                current = min(plan_data.missing_amount/((plan_data.duration + plan_data.remaining_time) /
                              3600)/(phases*230), plan_data.max_current)
            message = self.SCHEDULED_CHARGING_MAX_CURRENT.format(round(current, 2))
            submode = "instant_charging"
        else:
            # Wenn dynamische Tarife aktiv sind, prüfen, ob jetzt ein günstiger Zeitpunkt zum Laden
            # ist.
            if self.data.et.active and data.data.optional_data.et_provider_available():
                hour_list = data.data.optional_data.et_get_loading_hours(plan_data.duration, plan_data.remaining_time)
                log.debug(f"Günstige Ladezeiten: {hour_list}")
                if timecheck.is_list_valid(hour_list):
                    message = self.SCHEDULED_CHARGING_CHEAP_HOUR
                    current = plan_data.available_current
                    submode = "instant_charging"
                elif ((limit.selected == "soc" and soc <= limit.soc_limit) or
                      (limit.selected == "amount" and used_amount < limit.amount)):
                    message = self.SCHEDULED_CHARGING_EXPENSIVE_HOUR
                    current = min_current
                    submode = "pv_charging"
                    phases = control_parameter_phases
                else:
                    message = self.SCHEDULED_REACHED_LIMIT_SOC
            else:
                # Wenn SoC-Limit erreicht wurde, soll nicht mehr mit Überschuss geladen werden
                if limit.selected == "soc" and soc >= limit.soc_limit:
                    message = self.SCHEDULED_REACHED_LIMIT_SOC
                else:
                    message = self.SCHEDULED_CHARGING_USE_PV
                    current = min_current
                    submode = "pv_charging"
                    phases = control_parameter_phases
        return current, submode, message, phases

    def standby(self) -> Tuple[int, str, str]:
        return 0, "standby", "Keine Ladung, da der Lademodus Standby aktiv ist."

    def stop(self) -> Tuple[int, str, str]:
        return 0, "stop", "Keine Ladung, da der Lademodus Stop aktiv ist."
