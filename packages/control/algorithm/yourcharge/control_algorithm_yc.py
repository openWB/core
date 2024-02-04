import datetime
import logging
import sys

from dataclasses import dataclass, field
from typing import List

from control import data, yourcharge
from control.algorithm.yourcharge.status_handler import YcStatusHandler
from control.chargepoint.chargepoint import Chargepoint
from control.yourcharge import LmStatus, three_false_bool_factory

log = logging.getLogger(__name__)

@dataclass
class _AggregatedData:
    charging_on_phase_list: List[bool] = field(default_factory=three_false_bool_factory)
    number_of_charging_phases = 0
    is_charging: bool = False
    total_current_of_charging_phase_with_maximum_total_current: float = 0.0
    charging_phase_with_maximum_total_current: int = -1
    charging_ev_adjusted_for_this_cp: int = 0
    max_number_of_charging_vehicles_across_all_phases: int = 0
    maximum_total_current: float = 0
    phase_with_maximum_total_current: int = -1
    minimum_total_current: float = sys.float_info.max
    phase_with_minimum_total_current: int = -1
    maximum_imbalance_current: float = 0
    phase_with_maximum_imbalance_current: int = -1
    minimum_imbalance_current: float = sys.float_info.max
    phase_with_minimum_imbalance_current: int = -1

@dataclass
class _ExpectedChange:
    current: float = -1.0
    requested_at: datetime = datetime.datetime.utcnow()


class ControlAlgorithmYc:
    def __init__(self, cp_key: str, status_handler: YcStatusHandler) -> None:
        self._last_control_run = datetime.datetime(1, 1, 1, 0, 0, 0)
        self._internal_cp_key: str = cp_key
        self._internal_cp: Chargepoint = data.data.cp_data[self._internal_cp_key]
        self._previous_expected_charge_current: float = 0.0
        self._previous_charging_phase_info: List[bool] = [ False, False, False ]
        self._expected_change: _ExpectedChange = _ExpectedChange()
        self._status_handler = status_handler
        self._previous_justification = None

    def do_load_control(self) -> None:
        self._internal_cp = data.data.cp_data[self._internal_cp_key]
        # log.error(f"Internal CP now '{id(self._internal_cp)}'")

        if not data.data.yc_data.data.yc_control.fixed_charge_current is None:
            # handling of superseded, fixed charge current
            if data.data.yc_data.data.yc_control.fixed_charge_current < 0.0:
                # invalid or default value < 0.0
                self.set_current("Charging disapproved by yc_data.data.yc_control.fixed_charge_current", 0.0, yourcharge.LmStatus.DownByError)
            else:
                # fixed value >= 0.0 provided
                self.set_current("Fixed current requested by yc_data.data.yc_control.fixed_charge_current", data.data.yc_data.data.yc_control.fixed_charge_current, yourcharge.LmStatus.Superseded)
            return

        # check if control interval is actuall due
        now_it_is = datetime.datetime.utcnow()
        if (now_it_is - self._last_control_run).total_seconds() < data.data.yc_data.data.yc_config.minimum_adjustment_interval:
            log.debug(f"Control loop not yet due")
            return
        self._last_control_run = now_it_is

        # now we can start with actual load control calculation
        charging_phase_infos = self._aggregate_data()
        self._compute_current(charging_phase_infos)

    def _compute_current(self, charging_phase_infos: _AggregatedData) -> None:
        # check if the car has done the adjustment that it has last been asked for
        if self._expected_change.current >= 0.0:
            since_change: datetime.timedelta = datetime.datetime.utcnow() - self._expected_change.requested_at
            if since_change.total_seconds < data.data.yc_data.data.yc_config.minimum_adjustment_interval:
                log.error(f"Time after adjustment to {self._expected_change.current} A is ${since_change} < ${data.data.yc_data.data.yc_config.minimum_adjustment_interval} seconds: Skipping control loop")
                return

        # end charge on user-defined limits
        if self._is_user_limits_reached():
            self._call_set_current(charging_phase_infos, 0.0, LmStatus.DownByEnergyLimit)
            return

        # compute difference between allowed current on the total current of the phase that has the highest total current and is actually used for charging
    	# in floats for not to loose too much precision
        lldiff = (data.data.yc_data.data.yc_config.allowed_total_current_per_phase - charging_phase_infos.total_current_of_charging_phase_with_maximum_total_current) / charging_phase_infos.charging_ev_adjusted_for_this_cp

        # limit this initial difference to the maximum allowed charge current of the charge point
        if self._previous_expected_charge_current + lldiff > data.data.yc_data.data.yc_config.max_evse_current_allowed:
            log.error(f"_previous_expected_charge_current + lldiff > yc_config.max_evse_current_allowed ({self._previous_expected_charge_current} + {lldiff} > {data.data.yc_data.data.yc_config.max_evse_current_allowed}: Limiting to yc_config.max_evse_current_allowed")
            lldiff = data.data.yc_data.data.yc_config.max_evse_current_allowed - self._previous_expected_charge_current

        # see if we have to limit by allowed peak power (we have to if the value exists in ramdisk file and is > 0, ==0 means: peak limit disabled)
        if data.data.yc_data.data.yc_config.allowed_peak_power > 0.0:
            if data.data.yc_data.data.yc_control.total_power is None:
                raise ValueError(f"ERROR: Peak power limit set ({data.data.yc_data.data.yc_config.allowed_peak_power} W) but total power consumption not availble (yc_control.total_power={data.data.yc_data.data.yc_control.total_power} W): Immediately stopping charge and exiting")
            power_diff = (data.data.yc_data.data.yc_config.allowed_peak_power - data.data.yc_data.data.yc_control.total_power) / charging_phase_infos.charging_ev_adjusted_for_this_cp
            system_voltage = max(self._internal_cp.data.get.voltages)
            power_diff_as_current = power_diff / system_voltage / float(charging_phase_infos.number_of_charging_phases)
            if power_diff_as_current < lldiff:
                log.error(f"Difference to power limt of {data.data.yc_data.data.yc_config.allowed_peak_power} W is {power_diff} W (@ {system_voltage} V @ ${charging_phase_infos.charging_ev_adjusted_for_this_cp} charging vehicles) --> overriding $lldiff A to power_diff_as_current A on {charging_phase_infos.number_of_charging_phases} phase(s)")
                lldiff = power_diff_as_current

        log.error(f"yc_config.allowed_total_current_per_phase={data.data.yc_data.data.yc_config.allowed_total_current_per_phase} A, yc_config.allowed_peak_power={data.data.yc_data.data.yc_config.allowed_peak_power} W, yc_control.total_power={data.data.yc_data.data.yc_control.total_power} W, lldiff={lldiff} A")

        llneu = self._previous_expected_charge_current + lldiff

        log.error(f"total_current_of_charging_phase_with_maximum_total_current={charging_phase_infos.total_current_of_charging_phase_with_maximum_total_current} A, charging_ev_adjusted_for_this_cp={charging_phase_infos.charging_ev_adjusted_for_this_cp}, _previous_expected_charge_current={self._previous_expected_charge_current} A, lldiff={lldiff} A -> llneu={llneu} A")

        # handle load imbalance limit
        llneu = self._adjust_for_imbalance(charging_phase_infos, llneu)
        lldiff = llneu - self._previous_expected_charge_current

        # limit the change to +1, -1 or -3 if slow ramping is enabled, a value of 0 will be kept unchanged
        if data.data.yc_data.data.yc_config.slow_ramping:
            actual_adjustment = 0
            if lldiff >= 1.0:
                actual_adjustment = 1.0
            elif lldiff >= 0.0:
                actual_adjustment = lldiff
            elif lldiff <= -3.0:
                actual_adjustment = -3.0
            elif lldiff <= -0.5:
                actual_adjustment = -1.0

            # if we're not charging, we always start off with minimum supported current
            if not charging_phase_infos.is_charging:
                if lldiff < 0:
                    llneu = 0
                    log.error("Slow ramping: Not charging: Too few current left to start")
                else:
                    llneu = data.data.yc_data.data.yc_config.min_evse_current_allowed
                    log.error(f"Slow ramping: Not charging: Starting at minimal supported charge current {llneu} A")
            else:
                llneu = self._previous_expected_charge_current + actual_adjustment
                log.error(f"Slow ramping: Limiting adjustment to {self._previous_expected_charge_current} + {actual_adjustment} --> llneu = {llneu} A")
        else:
            # In "fast" mode the llneu might exceed the AllowedTotalCurrentPerPhase if the EV doesn't actually start consuming
            # the allowed current (and hence TotalCurrentConsumptionOnL1 doesn't increase).
            # For this case we limit to the total allowed current divided by the number of charging vehicals.
            # The resulting value might get further limited to maximalstromstaerke below.
            if llneu - 1.0 > data.data.yc_data.data.yc_config.allowed_total_current_per_phase:
                if llneu > self._previous_expected_charge_current:
                    log.error(f"Slave Mode: Fast ramping: EV seems to consume less than allowed (llneu={llneu} > yc_config.allowed_total_current_per_phase={data.data.yc_data.data.yc_config.allowed_total_current_per_phase} && llneu > _previous_expected_charge_current={self._previous_expected_charge_current}): Not changing allowed current")
                    llneu = self._previous_expected_charge_current
                else:
                    log.error(f"Fast ramping: EV seems to consume less than allowed (llneu={llneu} > yc_config.allowed_total_current_per_phase={data.data.yc_data.data.yc_config.allowed_total_current_per_phase} && llneu > _previous_expected_charge_current={self._previous_expected_charge_current}): Limiting allowed current to yc_config.allowed_total_current_per_phase={data.data.yc_data.data.yc_config.allowed_total_current_per_phase}")
                    llneu = data.data.yc_data.data.yc_config.allowed_total_current_per_phase
            else:
                log.error(f"Fast ramping: Setting llneu={llneu} A")

        self._call_set_current(charging_phase_infos, llneu, LmStatus.InLoop)


    def _adjust_for_imbalance(self, charging_phase_infos: _AggregatedData, llneu: float) -> None:
        ll_wanted_increase = llneu - self._previous_expected_charge_current

        #                         are we not contributing to maximum load phase                                       or                        we also contribute to minimal current phase                                     or        we're not charging
        if not charging_phase_infos.charging_on_phase_list[charging_phase_infos.phase_with_maximum_imbalance_current] or charging_phase_infos.charging_on_phase_list[charging_phase_infos.phase_with_minimum_imbalance_current] or not charging_phase_infos.is_charging:
            return llneu

        current_load_imbalance = charging_phase_infos.system_load_imbalance
        log.error(f"Load Imbalance: Current imbalance L{charging_phase_infos.phase_with_maximum_imbalance_current} - L{charging_phase_infos.phase_with_minimum_imbalance_current}: {data.data.yc_data.data.yc_control.imbalance_current_consumption[charging_phase_infos.phase_with_maximum_imbalance_current]} - {data.data.yc_data.data.yc_control.imbalance_current_consumption[charging_phase_infos.phase_with_minimum_imbalance_current]} = {current_load_imbalance} A (limit is {data.data.yc_data.data.yc_config.allowed_load_imbalance} A)")

        charging_ev_to_use = charging_phase_infos.charging_ev_adjusted_for_this_cp
        if charging_ev_to_use <= 0:
            charging_ev_to_use = 1

        imbalance_available = (data.data.yc_data.data.yc_config.allowed_load_imbalance - current_load_imbalance) / charging_ev_to_use
        log.error(f"Load Imbalance: Available imbalance {imbalance_available} A ({charging_ev_to_use} charging vehicles), wanted charge current increase ${ll_wanted_increase} A")

        if imbalance_available - ll_wanted_increase < 0.0:
            # need to reduce for imbalance
            llneu = self._previous_expected_charge_current + imbalance_available
            log.error(f"Load Imbalance: Adjusted to llneu={llneu} A for imbalance limit")
        else:
            log.error(f"Load Imbalance: No adjustment of llneu ({llneu} A) for load imbalance needed")

        return llneu


    def _is_user_limits_reached(self) -> bool:
        if data.data.yc_data.data.yc_config.energy_limit <= 0.0:
            log.debug("0 or negative energy limit setting: Energy limit disabled")
            return False

        log.error(f"Active energy limit: {data.data.yc_data.data.yc_config.energy_limit} Wh, already charged {self._status_handler.get_energy_charged_since_last_plugin()} kWh")

        if self._status_handler.get_energy_charged_since_last_plugin() > data.data.yc_data.data.yc_config.energy_limit:
            log.error("Energy limit reached: Disabling charge")
            return True

        log.debug("Energy limit not reached: Continue to charge")
        return False


    def _call_set_current(self, charging_phase_infos: _AggregatedData, current_to_set: float, status_reason: LmStatus) -> None:
        log.error(f"callSetCurent {current_to_set} {status_reason}")
        computed_reason = status_reason
        if current_to_set < data.data.yc_data.data.yc_config.min_evse_current_allowed:
            log.error(f"current_to_set={current_to_set} < yc_config.min_evse_current_allowed={data.data.yc_data.data.yc_config.min_evse_current_allowed} --> setze currentToSet=0")
            computed_reason = LmStatus.DownByLm
            current_to_set = 0
        if current_to_set > data.data.yc_data.data.yc_config.max_evse_current_allowed:
            log.error(f"current_to_set={current_to_set} > yc_config.max_evse_current_allowed={data.data.yc_data.data.yc_config.max_evse_current_allowed} --> setze currentToSet=yc_config.max_evse_current_allowed={data.data.yc_data.data.yc_config.max_evse_current_allowed}")
            current_to_set = data.data.yc_data.data.yc_config.max_evse_current_allowed
        if status_reason is None:
            if charging_phase_infos.is_charging:
                status_reason = computed_reason
            else:
                status_reason = LmStatus.DownByEv

        self.set_current("Regular load control", current_to_set, status_reason)


    def _aggregate_data(self) -> _AggregatedData:
        charging_phase_infos = _AggregatedData()

        # aggregate total currents
        for i, phase_total_current in enumerate(data.data.yc_data.data.yc_control.total_current_consumption):
            if phase_total_current > charging_phase_infos.maximum_total_current:
                charging_phase_infos.maximum_total_current = phase_total_current
                charging_phase_infos.phase_with_maximum_total_current = i
            if phase_total_current < charging_phase_infos.minimum_total_current:
                charging_phase_infos.minimum_total_current = phase_total_current
                charging_phase_infos.phase_with_minimum_total_current = i

        # aggregate imbalance currents
        for i, phase_imbal_current in enumerate(data.data.yc_data.data.yc_control.imbalance_current_consumption):
            if phase_imbal_current > charging_phase_infos.maximum_imbalance_current:
                charging_phase_infos.maximum_imbalance_current = phase_imbal_current
                charging_phase_infos.phase_with_maximum_imbalance_current = i
            if phase_imbal_current < charging_phase_infos.minimum_imbalance_current:
                charging_phase_infos.minimum_imbalance_current = phase_imbal_current
                charging_phase_infos.phase_with_minimum_imbalance_current = i

        charging_phase_infos.system_load_imbalance = charging_phase_infos.maximum_imbalance_current - charging_phase_infos.minimum_imbalance_current

        for i, phase_charge_current in enumerate(self._internal_cp.data.get.currents):
            # detect the phases on which WE are CURRENTLY charging and calculate dependent values
            if phase_charge_current > data.data.yc_data.data.yc_config.min_current_for_charge_detect:
                charging_phase_infos.is_charging |= True
                charging_phase_infos.charging_on_phase_list[i] = True
                charging_phase_infos.number_of_charging_phases = charging_phase_infos.number_of_charging_phases + 1
                if data.data.yc_data.data.yc_control.total_current_consumption[i] > charging_phase_infos.total_current_of_charging_phase_with_maximum_total_current:
                    charging_phase_infos.total_current_of_charging_phase_with_maximum_total_current = data.data.yc_data.data.yc_control.total_current_consumption[i]
                    charging_phase_infos.charging_phase_with_maximum_total_current = i
                if data.data.yc_data.data.yc_control.charging_vehicles[i] > charging_phase_infos.charging_ev_adjusted_for_this_cp:
                    charging_phase_infos.charging_ev_adjusted_for_this_cp = data.data.yc_data.data.yc_control.charging_vehicles[i]
            if data.data.yc_data.data.yc_control.charging_vehicles[i] > charging_phase_infos.max_number_of_charging_vehicles_across_all_phases:
                charging_phase_infos.max_number_of_charging_vehicles_across_all_phases = data.data.yc_data.data.yc_control.charging_vehicles[i]

        # store the phases on which we're currently charging for later use in case EV is no longer charging
        if charging_phase_infos.number_of_charging_phases > 0:
            self._previous_charging_phase_info = charging_phase_infos.charging_on_phase_list

        # if we're not charging at all, try smart fallback first: use the phase(s) on which we have last charged
        if charging_phase_infos.charging_phase_with_maximum_total_current == -1:
            # check if "last charging phase" usage is enabled; if not right away skip to the ultimate fallback
            if data.data.yc_data.data.yc_config.use_last_charging_phase:
                # iterate the phases and determine the last charging phase with maximum current
			    # if no last charging phase, leaves variables unchagned (i.e. at their default of 0 to trigger ultimate fallback)
                previous_number_of_charging_phases = 0
                for i, charging_on_phase in enumerate(self._previous_charging_phase_info):
                    if charging_on_phase:
                        previous_number_of_charging_phases = previous_number_of_charging_phases + 1
                        if data.data.yc_data.data.yc_control.total_current_consumption[i] > charging_phase_infos.total_current_of_charging_phase_with_maximum_total_current:
                            charging_phase_infos.total_current_of_charging_phase_with_maximum_total_current = data.data.yc_data.data.yc_control.total_current_consumption[i]
                            charging_phase_infos.charging_phase_with_maximum_total_current = i
                        if data.data.yc_data.data.yc_control.charging_vehicles[i] > charging_phase_infos.charging_ev_adjusted_for_this_cp:
                            charging_phase_infos.charging_ev_adjusted_for_this_cp = data.data.yc_data.data.yc_control.charging_vehicles[i]
                charging_phase_infos.number_of_charging_phases = previous_number_of_charging_phases

            # not supposed to use last charging phase or last charging phase info not available --> use maximum number of charging vehicles across all phases
            if charging_phase_infos.charging_phase_with_maximum_total_current == -1:
                charging_phase_infos.charging_ev_adjusted_for_this_cp = charging_phase_infos.max_number_of_charging_vehicles_across_all_phases
                for i, total_current in enumerate(data.data.yc_data.data.yc_control.total_current_consumption):
                    if total_current > charging_phase_infos.total_current_of_charging_phase_with_maximum_total_current:
                        charging_phase_infos.total_current_of_charging_phase_with_maximum_total_current = total_current
                        charging_phase_infos.charging_phase_with_maximum_total_current = i

        # ultimate check: raise
        if charging_phase_infos.charging_phase_with_maximum_total_current == -1:
            raise ValueError("Didn't set charging_phase_with_maximum_total_current")

    	# if we have no charging vehicles at all, assume ourself as charging (and avoid dev/0 error)
        if charging_phase_infos.charging_ev_adjusted_for_this_cp == 0:
            charging_phase_infos.charging_ev_adjusted_for_this_cp = 1

        # we must make sure that we don't leave NumberOfChargingPhases at 0 if we couldn't count it up to here so we have to assume worst-case (charging on all three phases - imbalance has less risk than total overload!)
        if charging_phase_infos.number_of_charging_phases == 0:
            charging_phase_infos.number_of_charging_phases = 3

        log.error(f"""
YC LM Info:
===========

System-wide:
Phase with maximum total current   : {charging_phase_infos.phase_with_maximum_total_current} @ {charging_phase_infos.maximum_total_current} A
Phase with minimum total current   : {charging_phase_infos.phase_with_minimum_total_current} @ {charging_phase_infos.minimum_total_current} A
Phase with maximum imbal. current  : {charging_phase_infos.phase_with_maximum_imbalance_current} @ {charging_phase_infos.maximum_imbalance_current} A
Phase with minimum imbal. current  : {charging_phase_infos.phase_with_minimum_imbalance_current} @ {charging_phase_infos.minimum_imbalance_current} A
Load imbalance                     : {charging_phase_infos.system_load_imbalance} A

Chargbox-related:
Metered current flow               : {self._internal_cp.data.get.currents} A (@{self._internal_cp.data.get.voltages}) V -> {self._internal_cp.data.get.power} W
Charging phase list                : {charging_phase_infos.charging_on_phase_list}
Number of charging phases          : {charging_phase_infos.number_of_charging_phases}
Highest total current across phases: {charging_phase_infos.total_current_of_charging_phase_with_maximum_total_current} (on phase {charging_phase_infos.charging_phase_with_maximum_total_current})
Charging EVs to consider           : {charging_phase_infos.charging_ev_adjusted_for_this_cp}
Max. charging EV over all phases   : {charging_phase_infos.max_number_of_charging_vehicles_across_all_phases}
""")

        return charging_phase_infos


    def set_current(self, justification: str, current: float, status: yourcharge.LmStatus):
        self._status_handler.update_lm_status(status)
        if abs(self._internal_cp.data.set.current - current) > 0.001 or (self._previous_justification != justification):
            log.error(f"{justification}: Setting CP '{self._internal_cp_key}' charge current to {current} A (status {status})")
            self._internal_cp.data.set.current = current
            self._internal_cp.chargepoint_module.set_current(current)
            self._previous_expected_charge_current = current
            self._previous_justification = justification
