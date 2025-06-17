from dataclasses import asdict, dataclass, field
import datetime
import logging
import traceback
from typing import List, Optional, Tuple

from control import data
from control.chargepoint.chargepoint_state import CHARGING_STATES
from control.chargepoint.charging_type import ChargingType
from control.chargepoint.control_parameter import ControlParameter
from control.ev.ev_template import EvTemplate
from dataclass_utils.factories import empty_list_factory
from helpermodules.abstract_plans import Limit, TimeChargingPlan, limit_factory, ScheduledChargingPlan
from helpermodules import timecheck
log = logging.getLogger(__name__)


def get_new_charge_template() -> dict:
    ct_default = asdict(ChargeTemplateData())
    return ct_default


def get_charge_template_default() -> dict:
    ct_default = asdict(ChargeTemplateData(name="Standard-Lade-Profil"))
    return ct_default


@dataclass
class ScheduledCharging:
    plans: List[ScheduledChargingPlan] = field(default_factory=empty_list_factory, metadata={
        "topic": ""})  # Dict[int,ScheduledChargingPlan] wird bei der dict to dataclass Konvertierung nicht unterstützt


@dataclass
class TimeCharging:
    active: bool = False
    plans: List[TimeChargingPlan] = field(default_factory=empty_list_factory, metadata={
        "topic": ""})  # Dict[int, TimeChargingPlan] wird bei der dict to dataclass Konvertierung nicht unterstützt


@dataclass
class EcoCharging:
    current: int = 6
    dc_current: float = 145
    limit: Limit = field(default_factory=limit_factory)
    max_price: float = 0.0002
    phases_to_use: int = 3


@dataclass
class InstantCharging:
    current: int = 16
    dc_current: float = 145
    limit: Limit = field(default_factory=limit_factory)
    phases_to_use: int = 3


@dataclass
class PvCharging:
    dc_min_current: float = 145
    dc_min_soc_current: float = 145
    feed_in_limit: bool = False
    limit: Limit = field(default_factory=limit_factory)
    min_current: int = 0
    min_soc_current: int = 10
    min_soc: int = 0
    phases_to_use: int = 0
    phases_to_use_min_soc: int = 3


def eco_charging_factory() -> EcoCharging:
    return EcoCharging()


def pv_charging_factory() -> PvCharging:
    return PvCharging()


def scheduled_charging_factory() -> ScheduledCharging:
    return ScheduledCharging()


def instant_charging_factory() -> InstantCharging:
    return InstantCharging()


@dataclass
class Chargemode:
    selected: str = "instant_charging"
    eco_charging: EcoCharging = field(default_factory=eco_charging_factory)
    pv_charging: PvCharging = field(default_factory=pv_charging_factory)
    scheduled_charging: ScheduledCharging = field(default_factory=scheduled_charging_factory)
    instant_charging: InstantCharging = field(default_factory=instant_charging_factory)


def time_charging_factory() -> TimeCharging:
    return TimeCharging()


def chargemode_factory() -> Chargemode:
    return Chargemode()


@dataclass
class ChargeTemplateData:
    id: int = 0
    name: str = "Lade-Profil"
    prio: bool = False
    load_default: bool = False
    time_charging: TimeCharging = field(default_factory=time_charging_factory)
    chargemode: Chargemode = field(default_factory=chargemode_factory)


def charge_template_data_factory() -> ChargeTemplateData:
    return ChargeTemplateData()


@dataclass
class SelectedPlan:
    remaining_time: float = 0
    duration: float = 0
    missing_amount: float = 0
    phases: int = 1
    plan: Optional[ScheduledChargingPlan] = None


@dataclass
class ChargeTemplate:
    """ Klasse der Lade-Profile
    """
    data: ChargeTemplateData = field(default_factory=charge_template_data_factory, metadata={
        "topic": ""})

    BUFFER = -1200  # nach mehr als 20 Min Überschreitung wird der Termin als verpasst angesehen
    CHARGING_PRICE_EXCEEDED = ("Der aktuelle Strompreis liegt über dem maximalen Strompreis. ")
    CHARGING_PRICE_LOW = "Laden, da der aktuelle Strompreis unter dem maximalen Strompreis liegt."

    TIME_CHARGING_NO_PLAN_CONFIGURED = "Zeitladen aktiviert, aber keine Zeitfenster konfiguriert."
    TIME_CHARGING_NO_PLAN_ACTIVE = "Keine Ladung, da kein Zeitfenster für Zeitladen aktiv ist."
    TIME_CHARGING_SOC_REACHED = "Kein Zeitladen, da der Soc bereits erreicht wurde."
    TIME_CHARGING_AMOUNT_REACHED = "Kein Zeitladen, da die Energiemenge bereits geladen wurde."

    def time_charging(self,
                      soc: Optional[float],
                      used_amount_time_charging: float,
                      charging_type: str) -> Tuple[int, str, Optional[str], Optional[str], int]:
        """ prüft, ob ein Zeitfenster aktiv ist und setzt entsprechend den Ladestrom
        """
        message = None
        sub_mode = "time_charging"
        id = None
        phases = None
        try:
            if self.data.time_charging.plans:
                plan = timecheck.check_plans_timeframe(self.data.time_charging.plans)
                if plan is not None:
                    current = plan.current if charging_type == ChargingType.AC.value else plan.dc_current
                    phases = plan.phases_to_use
                    id = plan.id
                    if plan.limit.selected == "soc" and soc and soc >= plan.limit.soc:
                        # SoC-Limit erreicht
                        current = 0
                        sub_mode = "stop"
                        message = self.TIME_CHARGING_SOC_REACHED
                    elif plan.limit.selected == "amount" and used_amount_time_charging >= plan.limit.amount:
                        # Energie-Limit erreicht
                        current = 0
                        sub_mode = "stop"
                        message = self.TIME_CHARGING_AMOUNT_REACHED
                else:
                    message = self.TIME_CHARGING_NO_PLAN_ACTIVE
                    current = 0
                    sub_mode = "stop"
            else:
                message = self.TIME_CHARGING_NO_PLAN_CONFIGURED
                current = 0
                sub_mode = "stop"
            return current, sub_mode, message, id, phases
        except Exception:
            log.exception("Fehler im ev-Modul "+str(self.data.id))
            return (0, "stop", "Keine Ladung, da da ein interner Fehler aufgetreten ist: "+traceback.format_exc(), None,
                    0)

    SOC_REACHED = "Keine Ladung, da der Soc bereits erreicht wurde."
    AMOUNT_REACHED = "Keine Ladung, da die Energiemenge bereits geladen wurde."

    def instant_charging(self,
                         soc: Optional[float],
                         used_amount: float,
                         charging_type: str) -> Tuple[int, str, Optional[str], int]:
        """ prüft, ob die Lademengenbegrenzung erreicht wurde und setzt entsprechend den Ladestrom.
        """
        message = None
        sub_mode = "instant_charging"
        try:
            instant_charging = self.data.chargemode.instant_charging
            phases = instant_charging.phases_to_use
            if charging_type == ChargingType.AC.value:
                current = instant_charging.current
            else:
                current = instant_charging.dc_current

            if instant_charging.limit.selected == "soc" and soc and soc >= instant_charging.limit.soc:
                current = 0
                sub_mode = "stop"
                message = self.SOC_REACHED
            elif instant_charging.limit.selected == "amount":
                if used_amount >= self.data.chargemode.instant_charging.limit.amount:
                    current = 0
                    sub_mode = "stop"
                    message = self.AMOUNT_REACHED
            return current, sub_mode, message, phases
        except Exception:
            log.exception("Fehler im ev-Modul "+str(self.data.id))
            return 0, "stop", "Keine Ladung, da da ein interner Fehler aufgetreten ist: "+traceback.format_exc(), 0

    PV_CHARGING_SOC_CHARGING = ("Ladung evtl. auch ohne PV-Überschuss, da der Mindest-SoC des Fahrzeugs noch nicht "
                                "erreicht wurde.")
    PV_CHARGING_MIN_CURRENT_CHARGING = "Ladung evtl. auch ohne PV-Überschuss, da minimaler Dauerstrom aktiv ist."

    def pv_charging(self,
                    soc: Optional[float],
                    min_current: int,
                    charging_type: str,
                    used_amount: float) -> Tuple[int, str, Optional[str], int]:
        """ prüft, ob Min-oder Max-Soc erreicht wurden und setzt entsprechend den Ladestrom.
        """
        message = None
        sub_mode = "pv_charging"
        try:
            pv_charging = self.data.chargemode.pv_charging
            phases = pv_charging.phases_to_use
            min_pv_current = (pv_charging.min_current if charging_type == ChargingType.AC.value
                              else pv_charging.dc_min_current)
            if pv_charging.limit.selected == "soc" and soc and soc > pv_charging.limit.soc:
                current = 0
                sub_mode = "stop"
                message = self.SOC_REACHED
            elif pv_charging.limit.selected == "amount" and used_amount >= pv_charging.limit.amount:
                current = 0
                sub_mode = "stop"
                message = self.AMOUNT_REACHED
            else:
                if pv_charging.min_soc != 0 and soc is not None and soc < pv_charging.min_soc:
                    if charging_type == ChargingType.AC.value:
                        current = pv_charging.min_soc_current
                    else:
                        current = pv_charging.dc_min_soc_current
                    sub_mode = "instant_charging"
                    message = self.PV_CHARGING_SOC_CHARGING
                    phases = pv_charging.phases_to_use_min_soc
                elif min_pv_current == 0:
                    # nur PV; Ampere darf nicht 0 sein, wenn geladen werden soll
                    current = min_current
                    sub_mode = "pv_charging"
                else:
                    # Min PV
                    current = min_pv_current
                    sub_mode = "instant_charging"
                    message = self.PV_CHARGING_MIN_CURRENT_CHARGING
            return current, sub_mode, message, phases
        except Exception:
            log.exception("Fehler im ev-Modul "+str(self.ct_num))
            return 0, "stop", "Keine Ladung, da ein interner Fehler aufgetreten ist: "+traceback.format_exc(), 1

    def eco_charging(self,
                     soc: Optional[float],
                     control_parameter: ControlParameter,
                     charging_type: str,
                     used_amount: float,
                     max_phases_hw: int) -> Tuple[int, str, Optional[str], int]:
        """ prüft, ob Min-oder Max-Soc erreicht wurden und setzt entsprechend den Ladestrom.
        """
        message = None
        sub_mode = "pv_charging"
        try:
            eco_charging = self.data.chargemode.eco_charging
            phases = eco_charging.phases_to_use
            current = eco_charging.current if charging_type == ChargingType.AC.value else eco_charging.dc_current

            if eco_charging.limit.selected == "soc" and soc and soc >= eco_charging.limit.soc:
                current = 0
                sub_mode = "stop"
                message = self.SOC_REACHED
            elif (eco_charging.limit.selected == "amount" and
                    used_amount >= self.data.chargemode.instant_charging.limit.amount):
                current = 0
                sub_mode = "stop"
                message = self.AMOUNT_REACHED
            elif data.data.optional_data.et_provider_available():
                if data.data.optional_data.et_charging_allowed(eco_charging.max_price):
                    sub_mode = "instant_charging"
                    message = self.CHARGING_PRICE_LOW
                    phases = max_phases_hw
                else:
                    current = control_parameter.min_current
                    message = self.CHARGING_PRICE_EXCEEDED
                    if control_parameter.state in CHARGING_STATES:
                        message += "Lädt mit Überschuss. "
            else:
                current = control_parameter.min_current
            return current, sub_mode, message, phases
        except Exception:
            log.exception("Fehler im ev-Modul "+str(self.data.id))
            return 0, "stop", "Keine Ladung, da ein interner Fehler aufgetreten ist: "+traceback.format_exc(), 0

    def scheduled_charging_recent_plan(self,
                                       soc: float,
                                       ev_template: EvTemplate,
                                       phases: int,
                                       used_amount: float,
                                       max_hw_phases: int,
                                       phase_switch_supported: bool,
                                       charging_type: str,
                                       chargemode_switch_timestamp: float,
                                       control_parameter: ControlParameter) -> Optional[SelectedPlan]:
        plans_diff_end_date = []
        for p in self.data.chargemode.scheduled_charging.plans:
            if p.active:
                if p.limit.selected == "soc" and soc is None:
                    raise ValueError("Um Zielladen mit SoC-Ziel nutzen zu können, bitte ein SoC-Modul konfigurieren "
                                     f"oder im Plan {p.name} als Begrenzung Energie einstellen.")
                try:
                    if ((p.limit.selected == "amount" and used_amount >= p.limit.amount) or
                            ((p.limit.selected == "soc" and soc >= p.limit.soc_scheduled) and
                             (p.limit.selected == "soc" and soc >= p.limit.soc_limit))):
                        plan_fulfilled = True
                    else:
                        plan_fulfilled = False
                    plans_diff_end_date.append(
                        {p.id: timecheck.check_end_time(p, chargemode_switch_timestamp, plan_fulfilled)})
                    log.debug(f"Verbleibende Zeit bis zum Zieltermin [s]: {plans_diff_end_date}, "
                              f"Plan erfüllt: {plan_fulfilled}")
                except Exception:
                    log.exception("Fehler im ev-Modul "+str(self.ct_num))
        if plans_diff_end_date:
            # ermittle den Key vom kleinsten value in plans_diff_end_date
            filtered_plans = [d for d in plans_diff_end_date if list(d.values())[0] is not None]
            if filtered_plans:
                plan_dict = min(filtered_plans, key=lambda x: list(x.values())[0])
                if plan_dict:
                    plan_id = list(plan_dict.keys())[0]
                    plan_end_time = list(plan_dict.values())[0]

                    plan = self.data.chargemode.scheduled_charging.plans[str(plan_id)]

                    remaining_time, missing_amount, phases, duration = self._calc_remaining_time(
                        plan, plan_end_time, soc, ev_template, used_amount, max_hw_phases, phase_switch_supported,
                        charging_type, control_parameter.phases)

                    return SelectedPlan(remaining_time=remaining_time,
                                        duration=duration,
                                        missing_amount=missing_amount,
                                        phases=phases,
                                        plan=plan)
            else:
                return None

    def _calc_remaining_time(self,
                             plan: ScheduledChargingPlan,
                             plan_end_time: float,
                             soc: Optional[float],
                             ev_template: EvTemplate,
                             used_amount: float,
                             max_hw_phases: int,
                             phase_switch_supported: bool,
                             charging_type: str,
                             control_parameter_phases) -> SelectedPlan:
        if plan.phases_to_use == 0:
            if max_hw_phases == 1:
                duration, missing_amount = self._calculate_duration(
                    plan, soc, ev_template.data.battery_capacity, used_amount, 1, charging_type, ev_template)
                remaining_time = plan_end_time - duration
                phases = 1
            elif phase_switch_supported is False:
                duration, missing_amount = self._calculate_duration(
                    plan, soc, ev_template.data.battery_capacity, used_amount, control_parameter_phases,
                    charging_type, ev_template)
                phases = control_parameter_phases
                remaining_time = plan_end_time - duration
            else:
                duration_3p, missing_amount = self._calculate_duration(
                    plan, soc, ev_template.data.battery_capacity, used_amount, 3, charging_type, ev_template)
                remaining_time_3p = plan_end_time - duration_3p
                duration_1p, missing_amount = self._calculate_duration(
                    plan, soc, ev_template.data.battery_capacity, used_amount, 1, charging_type, ev_template)
                remaining_time_1p = plan_end_time - duration_1p
                if remaining_time_1p < 0:
                    # Zeit reicht nicht mehr für einphasiges Laden
                    remaining_time = remaining_time_3p
                    duration = duration_3p
                    phases = 3
                else:
                    remaining_time = remaining_time_1p
                    duration = duration_1p
                    phases = 1
                log.debug(f"Dauer 1p: {duration_1p}, Dauer 3p: {duration_3p}")
        elif plan.phases_to_use == 3 or plan.phases_to_use == 1:
            duration, missing_amount = self._calculate_duration(
                plan, soc, ev_template.data.battery_capacity,
                used_amount, plan.phases_to_use, charging_type, ev_template)
            remaining_time = plan_end_time - duration
            phases = plan.phases_to_use

        log.debug(f"Verbleibende Zeit bis zum Ladestart [s]:{remaining_time}, Dauer [h]: {duration/3600}")
        return remaining_time, missing_amount, phases, duration

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
    SCHEDULED_CHARGING_USE_PV = ("Laden startet {}. Falls vorhanden, "
                                 "wird mit Überschuss geladen.")
    SCHEDULED_CHARGING_MAX_CURRENT = "Zielladen mit {}A. Der Ladestrom wurde erhöht, um das Ziel zu erreichen."
    SCHEDULED_CHARGING_LIMITED_BY_SOC = 'einen SoC von {}%'
    SCHEDULED_CHARGING_LIMITED_BY_AMOUNT = '{}kWh geladene Energie'
    SCHEDULED_CHARGING_IN_TIME = ('Zielladen mit mindestens {}A, um {} um {} zu erreichen. Falls vorhanden wird '
                                  'zusätzlich EVU-Überschuss geladen.')
    SCHEDULED_CHARGING_CHEAP_HOUR = "Zielladen, da ein günstiger Zeitpunkt zum preisbasierten Laden ist. {}"
    SCHEDULED_CHARGING_EXPENSIVE_HOUR = ("Zielladen ausstehend, da jetzt kein günstiger Zeitpunkt zum preisbasierten "
                                         "Laden ist. {} Falls vorhanden, wird mit Überschuss geladen.")

    def scheduled_charging_calc_current(self,
                                        selected_plan: Optional[SelectedPlan],
                                        soc: int,
                                        used_amount: float,
                                        control_parameter_phases: int,
                                        min_current: int,
                                        soc_request_interval_offset: int,
                                        charging_type: str,
                                        ev_template: EvTemplate) -> Tuple[float, str, str, int]:
        current = 0
        submode = "stop"
        if selected_plan is None:
            if len(self.data.chargemode.scheduled_charging.plans) == 0:
                return current, submode, self.SCHEDULED_CHARGING_NO_PLANS_CONFIGURED, control_parameter_phases
            else:
                return current, submode, self.SCHEDULED_CHARGING_NO_DATE_PENDING, control_parameter_phases
        plan = selected_plan.plan
        limit = plan.limit
        phases = selected_plan.phases
        if charging_type == ChargingType.AC.value:
            plan_current = plan.current
            max_current = ev_template.data.max_current_multi_phases
        else:
            plan_current = plan.dc_current
            max_current = ev_template.data.dc_max_current
        log.debug("Verwendeter Plan: "+str(plan.name))
        if limit.selected == "soc" and soc >= limit.soc_limit and soc >= limit.soc_scheduled:
            message = self.SCHEDULED_CHARGING_REACHED_LIMIT_SOC
        elif limit.selected == "soc" and limit.soc_scheduled <= soc < limit.soc_limit:
            message = self.SCHEDULED_CHARGING_REACHED_SCHEDULED_SOC
            current = min_current
            submode = "pv_charging"
            # bei Überschuss-Laden mit der Phasenzahl aus den control_parameter laden,
            # um die Umschaltung zu berücksichtigen.
            phases = plan.phases_to_use_pv
        elif limit.selected == "amount" and used_amount >= limit.amount:
            message = self.SCHEDULED_CHARGING_REACHED_AMOUNT
        elif 0 - soc_request_interval_offset < selected_plan.remaining_time < 300 + soc_request_interval_offset:
            # 5 Min vor spätestem Ladestart
            if limit.selected == "soc":
                limit_string = self.SCHEDULED_CHARGING_LIMITED_BY_SOC.format(limit.soc_scheduled)
            else:
                limit_string = self.SCHEDULED_CHARGING_LIMITED_BY_AMOUNT.format(limit.amount/1000)
            message = self.SCHEDULED_CHARGING_IN_TIME.format(plan_current, limit_string, plan.time)
            current = plan_current
            submode = "instant_charging"
        # weniger als die berechnete Zeit verfügbar
        elif selected_plan.remaining_time <= 0 - soc_request_interval_offset:
            if selected_plan.duration + selected_plan.remaining_time < 0:
                current = max_current
            else:
                current = min(selected_plan.missing_amount/((selected_plan.duration + selected_plan.remaining_time) /
                              3600)/(phases*230), max_current)
            message = self.SCHEDULED_CHARGING_MAX_CURRENT.format(round(current, 2))
            submode = "instant_charging"
        else:
            # Wenn dynamische Tarife aktiv sind, prüfen, ob jetzt ein günstiger Zeitpunkt zum Laden
            # ist.
            if plan.et_active:
                hour_list = data.data.optional_data.et_get_loading_hours(
                    selected_plan.duration, selected_plan.remaining_time)
                hours_message = ("Geladen wird zu folgenden Uhrzeiten: " +
                                 ", ".join([datetime.datetime.fromtimestamp(hour).strftime('%-H:%M')
                                           for hour in sorted(hour_list)])
                                 + ".")
                log.debug(f"Günstige Ladezeiten: {hour_list}")
                if timecheck.is_list_valid(hour_list):
                    message = self.SCHEDULED_CHARGING_CHEAP_HOUR.format(hours_message)
                    current = plan_current
                    submode = "instant_charging"
                elif ((limit.selected == "soc" and soc <= limit.soc_limit) or
                      (limit.selected == "amount" and used_amount < limit.amount)):
                    message = self.SCHEDULED_CHARGING_EXPENSIVE_HOUR.format(hours_message)
                    current = min_current
                    submode = "pv_charging"
                    phases = plan.phases_to_use_pv
                else:
                    message = self.SCHEDULED_REACHED_LIMIT_SOC
            else:
                # Wenn SoC-Limit erreicht wurde, soll nicht mehr mit Überschuss geladen werden
                if limit.selected == "soc" and soc >= limit.soc_limit:
                    message = self.SCHEDULED_REACHED_LIMIT_SOC
                else:
                    now = datetime.datetime.today()
                    start_time = now + datetime.timedelta(seconds=selected_plan.remaining_time)
                    if start_time.year == now.year and start_time.month == now.month and start_time.day == now.day:
                        message = self.SCHEDULED_CHARGING_USE_PV.format(
                            f"um {start_time.strftime('%-H:%M')} Uhr")
                    else:
                        message = self.SCHEDULED_CHARGING_USE_PV.format(
                            f"am {start_time.strftime('%d.%m')} um {start_time.strftime('%-H:%M')} Uhr")
                    current = min_current
                    submode = "pv_charging"
                    phases = plan.phases_to_use_pv
        return current, submode, message, phases

    def stop(self) -> Tuple[int, str, str]:
        return 0, "stop", "Keine Ladung, da der Lademodus Stop aktiv ist."
