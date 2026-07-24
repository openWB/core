import datetime
import logging
from typing import Callable, Dict, List, Optional, Tuple

from control import data
from control.algorithm.utils import get_medium_charging_current
from control.chargemode import Chargemode
from control.chargepoint.chargepoint_state import CHARGING_STATES, ChargepointState
from control.consumer.consumer_data import ConsumerData, ConsumerUsage, ResetModes, WaitForStartStates
from control.load_protocol import Load
from helpermodules import timecheck
from helpermodules.abstract_plans import ScheduledPlanConsumer
from helpermodules.phase_handling import convert_single_evu_phase_to_cp_phase, voltages_mean
from modules.common.configurable_consumer import ConfigurableConsumer

log = logging.getLogger(__name__)


class Consumer(Load):
    PAUSE_BETWEEN_WAIT_FOR_START_TEST_RUNS = 3600

    def __init__(self, index: int):
        self.num = index
        self.data: ConsumerData = ConsumerData()
        self.module: ConfigurableConsumer = None
        self.chargemode_changed: bool = False
        self.submode_changed: bool = False

    def set_state_and_log(self, message: Optional[str]) -> None:
        if message:
            log.info(f"Verbraucher {self.num}: {message}")
            if self.data.get.state_str is None:
                self.data.get.state_str = message
            elif message not in self.data.get.state_str:
                self.data.get.state_str += f" {message}"

    def setup_values_at_start(self):
        self.data.set.state_str_prev = self.data.get.state_str
        self.data.get.state_str = None
        self.data.set.current_prev = self.data.set.current

    def update(self):
        try:
            self.setup_values_at_start()
            if self.data.usage.type == ConsumerUsage.METER_ONLY:
                return
            else:
                if self.data.get.voltages is None:
                    self.data.get.voltages = [230 for i in range(0, self.data.config.connected_phases)]
                if self.data.get.currents is None:
                    self.data.get.currents = [0]*3
                    for i in range(0, self.data.config.connected_phases):
                        self.data.get.currents[i] = (self.data.get.power /
                                                     self.data.config.connected_phases /
                                                     self.data.get.voltages[i])
                self.data.get.phases_in_use = self.data.config.connected_phases
                self.data.set.phases_to_use = self.data.config.connected_phases
                self.data.get.charge_state = True if self.data.get.power > 0 else False
                self.reset_chargemode_at_time()
                self.is_switch_interval_elapsed()
                min_current, required_current, message, mode, submode = self.get_parameter()
                self.set_mode_changed(submode, mode)
                self.set_control_parameter(min_current, required_current,
                                           self.data.config.connected_phases, submode, mode)
                self.set_state_and_log(message)
                self.process_on_time()
                log.debug(f"Verbraucher {self.num}: Sollstrom {required_current}, "
                          f"min. Ist-Strom {max(self.data.get.currents)},"
                          f" Modus {mode}, Submodus {submode}, {message}")
        except Exception:
            log.exception(f"Fehler bei Verbraucher {self.num}")

    def process_on_time(self):
        if self.data.get.charge_state:
            self.data.set.on_time += data.data.general_data.data.control_interval
            if self.data.control_parameter.timestamp_charge_start is None:
                self.data.control_parameter.timestamp_charge_start = timecheck.create_timestamp()
        elif self.data.get.charge_state is False:
            self.data.control_parameter.timestamp_charge_start = None

    def reset_timestamp_start(self):
        self.data.control_parameter.timestamp_charge_start = None

    def reset_on_time(self):
        self.data.set.on_time = 0

    def is_switch_interval_elapsed(self):
        if (timecheck.create_timestamp() < self.data.set.timestamp_last_current_set + self.data.config.min_interval and
                # wenn kein Betrieb, darf eingeschaltet werden, auch wenn das Intervall noch nicht abgelaufen ist
                self.data.control_parameter.state != ChargepointState.NO_CHARGING_ALLOWED and
                (self.data.usage.wait_for_start_active is False or
                (self.data.usage.wait_for_start_active and
                self.data.set.wait_for_start_state == WaitForStartStates.START_SIGNAL_RECEIVED))):
            self.data.set.switch_interval_elapsed = False
        else:
            self.data.set.switch_interval_elapsed = True

    PRICE_LIMIT_EXCEEDED = "Preislimit für Verbraucher aktiv, aktueller Preis zu hoch."
    PRICE_LIMIT_EXCEEDED_CONTINOUS_STILL_RUNNING = ("Preislimit für Verbraucher aktiv, aktueller Preis zu hoch. "
                                                    "Verbraucher läuft weiter, da der Verbraucher nicht abgeschaltet "
                                                    "werden darf.")
    BELOW_PRICE_LIMIT = "Preislimit für Verbraucher aktiv, aktueller Preis in Ordnung."
    SURPLUS_CONTINOUS_STILL_RUNNING = ("Verbraucher läuft ggf auch ohne ausreichend Überschuss weiter, da der "
                                       "Verbraucher nicht abgeschaltet werden darf.")

    def get_parameter(self) -> Tuple[float, float, Optional[str], Optional[Chargemode], Chargemode]:
        if self.data.set.switch_interval_elapsed is False:
            log.debug("Intervall für neuen Schaltbefehl nicht abgelaufen.")
            return (0,
                    0,
                    self.data.set.state_str_prev,
                    self.data.control_parameter.chargemode,
                    self.data.control_parameter.submode)

        if self.data.usage.type == ConsumerUsage.SUSPENDABLE_TUNABLE:
            min_current = self.data.config.min_current
        else:
            min_current = self._convert_power_to_current(self.data.config.max_power)
        required_current = 0
        submode = Chargemode.STOP
        mode = self.data.usage.chargemode
        message = None
        if self.data.usage.chargemode == Chargemode.SCHEDULED_CHARGING:
            required_current, tmp_message, submode = self.wait_for_start_handler(self.scheduled_charging)
            message = f"{tmp_message or ''}".strip()
        if submode != Chargemode.INSTANT_CHARGING and self.data.usage.time_charging.active:
            required_current, tmp_message, submode = self.time_charging()
            # Info vom Zielladen erhalten
            message = f"{message or ''} {tmp_message or ''}".strip()
        if required_current == 0:
            if self.data.usage.chargemode == Chargemode.INSTANT_CHARGING:
                required_current, tmp_message, submode = self.instant_charging()
            elif self.data.usage.chargemode == Chargemode.ECO_CHARGING:
                required_current, tmp_message, submode = self.wait_for_start_handler(self.eco_charging)
            elif self.data.usage.chargemode == Chargemode.PV_CHARGING:
                required_current, tmp_message, submode = self.wait_for_start_handler(self.pv_charging)
            else:
                tmp_message = None
            message = f"{message or ''} {tmp_message or ''}".strip()
        if self.data.usage.chargemode == Chargemode.STOP:
            required_current, message, submode = self.stop()
        return min_current, required_current, message, mode, submode

    def _parse_required_current_by_usage(self, required_current: float) -> float:
        if self.data.usage.type in [ConsumerUsage.CONTINUOUS, ConsumerUsage.SUSPENDABLE_ONOFF]:
            if self.data.get.charge_state:
                return get_medium_charging_current(self.data.get.currents)
            else:
                return self._convert_power_to_current(self.data.config.max_power)
        else:
            return required_current

    def _convert_power_to_current(self, power: float) -> float:
        phases = self.data.config.connected_phases or 1
        voltage = voltages_mean(self.data.get.voltages) or 230.0
        return power / phases / voltage

    BUFFER_AFTER_END_TIME = -1200  # nach mehr als 20 Min Überschreitung wird der Termin als verpasst angesehen
    BUFFER_START_EARLIER = 600  # 10 Min vor dem geplanten Start kann begonnen werden

    def scheduled_charging(self) -> Tuple[float, Optional[str], Chargemode]:
        plan_data, remaining_time, duration = self._find_recent_plan(self.data.usage.scheduled_charging.plans)
        if plan_data:
            self.data.control_parameter.current_plan = plan_data.id
        else:
            self.data.control_parameter.current_plan = None
        return self.scheduled_charging_calc_current(
            plan_data,
            remaining_time,
            duration)

    def _find_recent_plan(self,
                          plans: List[ScheduledPlanConsumer]) -> Tuple[Optional[ScheduledPlanConsumer], float, float]:
        plans_diff_end_date: List[Dict[int, float]] = []
        for p in plans:
            try:
                plans_diff_end_date.append(
                    {p.id: timecheck.check_end_time(p, self.BUFFER_AFTER_END_TIME)})
                log.debug(f"Verbleibende Zeit bis zum Zieltermin [s]: {plans_diff_end_date}")
            except Exception:
                log.exception("Fehler im ev-Modul "+str(self.num))
        if plans_diff_end_date:
            # ermittle den Key vom kleinsten value in plans_diff_end_date
            # filtered_plans = [d for d in plans_diff_end_date if list(d.values())[0] is not None]
            # if filtered_plans:
            sorted_plans = sorted(plans_diff_end_date, key=lambda x: list(x.values())[0])
            for p in sorted_plans:
                if self.BUFFER_AFTER_END_TIME < list(p.values())[0]:
                    plan_dict = p
                    break
            else:
                return None, 0, 0
            plan_id = list(plan_dict.keys())[0]
            diff_end_date = list(plan_dict.values())[0]

            for p in plans:
                if p.id == plan_id:
                    plan = p
                    break
            else:
                raise Exception(f"Verbraucher {self.num} konnte plan_id {plan_id} keine Plan zuordnen.")

            remaining_time, duration = self._calc_remaining_time(plan, diff_end_date)

            return plan, remaining_time, duration
        return None, 0, 0

    def _calc_remaining_time(self,
                             plan: ScheduledPlanConsumer,
                             diff_end_date: float) -> Tuple[float, float]:
        duration = plan.duration - self.data.set.on_time
        remaining_time = diff_end_date - duration

        log.debug(f"Verbleibende Zeit bis zum Ladestart [s]:{remaining_time}, Dauer [h]: {duration/3600}")
        return remaining_time, duration

    SCHEDULED_REACHED_MAX_ON_TIME = ("Ziel erreicht, da das Gerät die gewünschte Dauer in Betrieb war.")
    SCHEDULED_CHARGING_NO_PLANS_CONFIGURED = "Kein Ziel, da keine Ziel-Termine konfiguriert sind."
    SCHEDULED_CHARGING_NO_DATE_PENDING = "Kein Ziel, da kein Ziel-Termin ansteht. "
    SCHEDULED_CHARGING_USE_PV = "Betrieb startet {}. Falls vorhanden, wird Überschuss verwendet. "
    SCHEDULED_CHARGING_CHEAP_HOUR = "Ziel, da ein günstiger Zeitpunkt für den preisbasierten Betrieb ist. {}"
    SCHEDULED_CHARGING_EXPENSIVE_HOUR = (
        "Ziel ausstehend, da jetzt kein günstiger Zeitpunkt für den preisbasierten "
        "Betrieb ist. {} Falls vorhanden, wird Überschuss verwendet. ")

    def scheduled_charging_calc_current(
            self,
            plan: Optional[ScheduledPlanConsumer],
            remaining_time: float,
            duration: float) -> Tuple[float, Optional[str], Chargemode]:
        required_current = 0
        message = None
        if plan is None:
            if len(self.data.usage.scheduled_charging.plans) == 0:
                return 0, self.SCHEDULED_CHARGING_NO_PLANS_CONFIGURED, Chargemode.STOP
            else:
                return 0, self.SCHEDULED_CHARGING_NO_DATE_PENDING, Chargemode.STOP
        if (self.BUFFER_AFTER_END_TIME < remaining_time < 0 and
                self.data.set.wait_for_start_state == WaitForStartStates.START_SIGNAL_RECEIVED):
            self.reset_wait_for_start()
        if duration <= 0:
            message = self.SCHEDULED_REACHED_MAX_ON_TIME
            submode = Chargemode.STOP
        elif remaining_time < self.BUFFER_START_EARLIER:
            submode = Chargemode.INSTANT_CHARGING
            required_current = self._parse_required_current_by_usage(
                self._convert_power_to_current(self.data.config.max_power))
        else:
            # Wenn dynamische Tarife aktiv sind, prüfen, ob jetzt ein günstiger Zeitpunkt zum Laden
            # ist.
            if data.data.optional_data.data.electricity_pricing.configured:
                def get_hours_message() -> str:
                    def end_of_today_timestamp() -> float:
                        return datetime.datetime.now().replace(
                            hour=23, minute=59, second=59, microsecond=999000).timestamp()

                    def is_loading_hour(hour_list: List[int]) -> bool:
                        return data.data.optional_data.ep_is_charging_allowed_hours_list(hour_list)

                    def convert_loading_hours_to_string(hour_list: List[datetime.datetime]) -> str:
                        if 1 < len(hour_list):
                            times_string = ", ".join(hour.strftime('%-H:%M') for hour in hour_list[:-1])
                            return times_string + " und " + hour_list[-1].strftime('%-H:%M')
                        else:
                            return ", ".join(hour.strftime('%-H:%M') for hour in hour_list)
                    midnight = end_of_today_timestamp()
                    loading_times_today = [datetime.datetime.fromtimestamp(hour)
                                           for hour in sorted(hour_list) if hour <= midnight]
                    loading_times_today = (loading_times_today[1:]
                                           if is_loading_hour(hour_list) else loading_times_today)
                    loading_times_tomorrow = [datetime.datetime.fromtimestamp(hour)
                                              for hour in sorted(hour_list) if hour > midnight]

                    parts: List[str] = []

                    if is_loading_hour(hour_list):
                        parts.append("jetzt")

                    if 0 < len(loading_times_today):
                        if parts:
                            parts.append(" und ")
                        parts.append(f"heute {convert_loading_hours_to_string(loading_times_today)}")

                    if 0 < len(loading_times_tomorrow):
                        if parts:
                            parts.append(" sowie ")
                        parts.append(f"morgen {convert_loading_hours_to_string(loading_times_tomorrow)}")

                    loading_message = "Eingeschaltet wird " + "".join(parts)
                    return loading_message + '.'

                hour_list = data.data.optional_data.ep_get_loading_hours(duration, duration + remaining_time)

                log.debug(f"Günstige Ladezeiten: {hour_list}")
                if data.data.optional_data.ep_is_charging_allowed_hours_list(hour_list):
                    message = self.SCHEDULED_CHARGING_CHEAP_HOUR.format(get_hours_message())
                    submode = Chargemode.INSTANT_CHARGING
                    required_current = self._parse_required_current_by_usage(
                        self._convert_power_to_current(self.data.config.max_power))
                else:
                    message = self.SCHEDULED_CHARGING_EXPENSIVE_HOUR.format(get_hours_message())
                    submode = Chargemode.PV_CHARGING
                    required_current = self._parse_required_current_by_usage(self.data.config.min_current)
            else:
                now = datetime.datetime.today()
                start_time = now + datetime.timedelta(seconds=remaining_time)
                if start_time.year == now.year and start_time.month == now.month and start_time.day == now.day:
                    message = self.SCHEDULED_CHARGING_USE_PV.format(
                        f"um {start_time.strftime('%-H:%M')} Uhr")
                else:
                    message = self.SCHEDULED_CHARGING_USE_PV.format(
                        f"am {start_time.strftime('%d.%m')} um {start_time.strftime('%-H:%M')} Uhr")
                submode = Chargemode.PV_CHARGING
                required_current = self._parse_required_current_by_usage(self.data.config.min_current)
        return required_current, message, submode

    TIME_CHARGING_MIN_BAT_SOC_REACHED = ("Betrieb mit Zeitladen nach Speicher-SoC nicht möglich, da der SoC des"
                                         " Speichers unter dem minimalen SoC liegt.")
    TIME_CHARGING_CONFLICT_ACTIVE_BAT_CONTROL = (
        "Betrieb mit Zeitladen nicht möglich, da eine aktive Batteriesteuerung einen Konflikt verursacht.")
    TIME_CHARGING_NO_PLAN_ACTIVE = "Betrieb mit Zeitladen nicht möglich, da kein Plan aktiv ist."
    TIME_CHARGING_NO_PLAN_CONFIGURED = "Betrieb mit Zeitladen nicht möglich, da kein Plan konfiguriert ist."

    def time_charging(self) -> Tuple[float, Optional[str], Chargemode]:
        required_current = 0
        message = None
        submode = Chargemode.STOP
        if self.data.usage.time_charging.plans:
            plan = timecheck.check_plans_timeframe(self.data.usage.time_charging.plans)
            if plan is not None:
                if plan.min_bat_soc is not None and data.data.bat_all_data.data.config.configured:
                    if data.data.bat_all_data.time_charging_min_bat_soc_allowed():
                        if data.data.bat_all_data.data.get.soc < plan.min_bat_soc:
                            message = self.TIME_CHARGING_MIN_BAT_SOC_REACHED
                        else:
                            log.debug(
                                "Zeitladen: minimaler Speicher-SoC überschritten, Laden mit Zeitladen möglich.")
                            required_current = self._parse_required_current_by_usage(
                                self._convert_power_to_current(self.data.config.max_power))
                            submode = Chargemode.TIME_CHARGING
                    else:
                        message = self.TIME_CHARGING_CONFLICT_ACTIVE_BAT_CONTROL
                else:
                    required_current = self._parse_required_current_by_usage(
                        self._convert_power_to_current(self.data.config.max_power))
                    submode = Chargemode.TIME_CHARGING
            else:
                message = self.TIME_CHARGING_NO_PLAN_ACTIVE
        else:
            message = self.TIME_CHARGING_NO_PLAN_CONFIGURED
        return required_current, message, submode

    def instant_charging(self) -> Tuple[float, Optional[str], Chargemode]:
        required_current = self._parse_required_current_by_usage(
            self._convert_power_to_current(self.data.config.max_power))
        message = None
        submode = Chargemode.INSTANT_CHARGING
        return required_current, message, submode

    CHARGING_PRICE_EXCEEDED = "Der aktuelle Strompreis liegt über dem maximalen Strompreis. "
    CHARGING_PRICE_LOW = "Betrieb, da der aktuelle Strompreis unter dem maximalen Strompreis liegt."

    def eco_charging(self) -> Tuple[float, Optional[str], Chargemode]:
        message = None
        if data.data.optional_data.data.electricity_pricing.configured:
            if data.data.optional_data.ep_is_charging_allowed_price_threshold(
                    self.data.usage.eco_charging.price_limit):
                required_current = self._parse_required_current_by_usage(
                    self._convert_power_to_current(self.data.config.max_power))
                message = self.CHARGING_PRICE_LOW
                submode = Chargemode.INSTANT_CHARGING
            else:
                required_current = self._parse_required_current_by_usage(self.data.config.min_current)
                message = self.CHARGING_PRICE_EXCEEDED
                if self.data.control_parameter.state in CHARGING_STATES:
                    message += "Lädt mit Überschuss. "
                submode = Chargemode.PV_CHARGING
        else:
            required_current = self._parse_required_current_by_usage(self.data.config.min_current)
            submode = Chargemode.PV_CHARGING
        return required_current, message, submode

    def pv_charging(self) -> Tuple[float, Optional[str], Chargemode]:
        required_current = self._parse_required_current_by_usage(self.data.config.min_current)
        message = None
        submode = Chargemode.PV_CHARGING
        return required_current, message, submode

    def stop(self) -> Tuple[float, Optional[str], Chargemode]:
        required_current = 0
        message = "Verbraucher im Modus Stop. "
        submode = Chargemode.STOP
        return required_current, message, submode

    WAIT_FOR_DEVICE_START = "Warte auf Gerätestart, Gerät eingeschaltet lassen."
    WAIT_FOR_STOPPED_DEVICE = "Gerätestart erkannt, warte auf gestopptes Gerät."
    DEVICE_WAITING_FOR_START = ("Gerätestart erkannt. "
    "Warte auf Erreichen der Einschaltschwelle, um das Gerät zu starten.")

    def wait_for_start_handler(
            self, func: Callable[[], Tuple[float, Optional[str], Chargemode]]
    ) -> Tuple[float, Optional[str], Chargemode]:
        if self.data.usage.wait_for_start_active:
            if self.data.set.wait_for_start_state == WaitForStartStates.WAIT_FOR_DEVICE_START:
                # mit Minimalstrom prüfen, damit Standby-Geräte nicht als laufend erkannt werden
                if max(self.data.get.currents) > self.data.config.min_current:
                    self.data.set.wait_for_start_state = WaitForStartStates.WAIT_FOR_STOPPED_DEVICE
                    required_current = 0
                    message = self.WAIT_FOR_STOPPED_DEVICE
                    submode = Chargemode.STOP
                else:
                    required_current = self._parse_required_current_by_usage(
                        self._convert_power_to_current(self.data.config.max_power))
                    message = self.WAIT_FOR_DEVICE_START
                    submode = Chargemode.INSTANT_CHARGING
            elif self.data.set.wait_for_start_state == WaitForStartStates.WAIT_FOR_STOPPED_DEVICE:
                # mit Minimalstrom prüfen, damit Standby-Geräte nicht als laufend erkannt werden
                if max(self.data.get.currents) < self.data.config.min_current:
                    self.data.set.wait_for_start_state = WaitForStartStates.DEVICE_WAITING_FOR_START
                    required_current, message, submode = func()
                    message = self.DEVICE_WAITING_FOR_START + " " + (message if message else "")
                else:
                    self.data.set.wait_for_start_state = WaitForStartStates.WAIT_FOR_STOPPED_DEVICE
                    required_current = 0
                    message = self.WAIT_FOR_STOPPED_DEVICE
                    submode = Chargemode.STOP
            elif self.data.set.wait_for_start_state == WaitForStartStates.DEVICE_WAITING_FOR_START:
                # mit Minimalstrom prüfen, damit Standby-Geräte nicht als laufend erkannt werden
                if max(self.data.get.currents) > self.data.config.min_current:
                    self.data.set.wait_for_start_state = WaitForStartStates.START_SIGNAL_RECEIVED
                    required_current, message, submode = func()
                else:
                    required_current, message, submode = func()
                    message = self.DEVICE_WAITING_FOR_START + " " + (message if message else "")
            elif self.data.set.wait_for_start_state == WaitForStartStates.START_SIGNAL_RECEIVED:
                required_current, message, submode = func()
            else:
                raise ValueError(
                    f"Ungültiger wait_for_start_state {self.data.set.wait_for_start_state} für Verbraucher {self.num}")
        else:
            required_current, message, submode = func()
        return required_current, message, submode

    def reset_wait_for_start(self):
        self.data.set.wait_for_start_state = WaitForStartStates.WAIT_FOR_DEVICE_START

    def midnight_handler(self):
        self.reset_chargemode_at_midnight()
        self.reset_wait_for_start()
        self.reset_timestamp_start()
        self.reset_on_time()

    def reset_chargemode_at_midnight(self):
        if self.data.usage.reset_chargemode.mode == ResetModes.MIDNIGHT:
            if self.data.usage.chargemode != self.data.usage.reset_chargemode.chargemode:
                log.info(f"Zurücksetzen des Lademodus auf {self.data.usage.reset_chargemode.chargemode} "
                         f"für Verbraucher {self.num} um Mitternacht.")
                self.data.usage.chargemode = self.data.usage.reset_chargemode.chargemode

    def reset_chargemode_at_time(self):
        if (self.data.usage.reset_chargemode.mode == ResetModes.TIME and
                self.data.usage.reset_chargemode.time is not None):
            if (self.data.usage.reset_chargemode.time < timecheck.create_timestamp() <
                    self.data.usage.reset_chargemode.time + data.data.general_data.data.control_interval):
                if self.data.usage.chargemode != self.data.usage.reset_chargemode.chargemode:
                    log.info(f"Zurücksetzen des Lademodus auf {self.data.usage.reset_chargemode.chargemode} "
                             f"für Verbraucher {self.num} um definierte Zeit.")
                    self.data.usage.chargemode = self.data.usage.reset_chargemode.chargemode

    def set_control_parameter(self,
                              min_current: float,
                              required_current: float,
                              phases: int,
                              submode: Chargemode,
                              mode: Optional[Chargemode]):
        self.data.control_parameter.min_current = min_current
        self.data.control_parameter.required_current = required_current
        self.data.control_parameter.phases = phases
        self.data.control_parameter.submode = submode
        self.data.control_parameter.chargemode = mode
        control_parameter = self.data.control_parameter
        try:
            for i in range(0, phases):
                evu_phase = convert_single_evu_phase_to_cp_phase(self.data.config.phase_1, i)
                control_parameter.required_currents[evu_phase] = required_current
        except KeyError:
            control_parameter.required_currents = [required_current]*3
            self.set_state_and_log("Bitte in den Verbraucher-Einstellungen die Einstellung 'Phase 1 des Ladekabels'" +
                                   " angeben. Andernfalls wird der benötigte Strom auf allen 3 Phasen vorgehalten, " +
                                   "was ggf eine unnötige Reduktion der Ladeleistung zur Folge hat.")
        self.data.set.required_power = sum(
            [c * v for c, v in zip(control_parameter.required_currents, self.data.get.voltages)])

    def is_charging_stop_allowed(self) -> bool:
        return self.data.usage.type != ConsumerUsage.CONTINUOUS

    def set_mode_changed(self, submode: Chargemode, mode: Optional[Chargemode]) -> None:
        self.submode_changed = (submode != self.data.control_parameter.submode)
        if ((submode == Chargemode.TIME_CHARGING and
             self.data.control_parameter.chargemode != Chargemode.TIME_CHARGING) or
                (submode != Chargemode.TIME_CHARGING and
                 self.data.control_parameter.chargemode != mode)):
            self.chargemode_changed = True
            log.debug("Änderung des Lademodus")
            self.data.control_parameter.timestamp_chargemode_changed = timecheck.create_timestamp()
            self.reset_wait_for_start()
        else:
            self.chargemode_changed = False
