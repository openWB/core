#!/usr/bin/env python3
import logging
import math
import time
from requests import HTTPError

from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_counter_value_store
from modules.devices.tesla.tesla.config import TeslaCounterSetup
from modules.devices.tesla.tesla.http_client import PowerwallHttpClient

log = logging.getLogger(__name__)


class TeslaCounter(AbstractCounter):
    def __init__(self, component_config: TeslaCounterSetup) -> None:
        self.component_config = component_config

        # Throttle diagnostic logging (to avoid log spam in a 10s polling cycle)
        self._last_energy_debug_log_ts: float = 0.0

    def initialize(self) -> None:
        self.store = get_counter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))

    @staticmethod
    def _safe_float(val, default: float = 0.0) -> float:
        try:
            if val is None:
                return default
            return float(val)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _nearly_zero(x: float, eps: float = 1e-9) -> bool:
        return abs(x) < eps

    def _calc_currents_and_pf_from_pqu(
        self, voltages: list[float], p_list: list[float], q_list: list[float]
    ) -> tuple[list[float], list[float]]:
        """
        Calculates signed currents (A) and signed power factors per phase from P/Q/U.
        Convention:
          - sign of current follows sign of active power P (import +, export -)
          - PF = P / S (signed)
          - S = sqrt(P^2 + Q^2)
          - I = S / U  (signed via P)
        """
        currents: list[float] = [0.0, 0.0, 0.0]
        pfs: list[float] = [0.0, 0.0, 0.0]

        for i in range(3):
            u = self._safe_float(voltages[i], 0.0)
            p = self._safe_float(p_list[i], 0.0)
            q = self._safe_float(q_list[i], 0.0)

            if self._nearly_zero(u):
                currents[i] = 0.0
                pfs[i] = 0.0
                continue

            s = math.sqrt(p * p + q * q)  # apparent power [VA]

            if self._nearly_zero(s):
                currents[i] = 0.0
                pfs[i] = 0.0
                continue

            # signed PF: magnitude P/S, sign from P
            pf = p / s
            pfs[i] = pf

            # signed current: magnitude S/U, sign from P
            i_mag = s / u
            currents[i] = i_mag if p >= 0 else -i_mag

        return currents, pfs

    def update(self, client: PowerwallHttpClient, aggregate):
        # read firmware version only at startup or after cookie renewal
        if getattr(client, "cookie_renewed", False) or not getattr(self.store, "firmware", None):
            try:
                status = client.get_json("/api/status", fail_fast=False)
                if isinstance(status, dict):
                    self.store.firmware = status.get("version", "")
                    log.debug("Firmware: %s", self.store.firmware)
            except Exception:
                # Non-critical: ignore status retrieval errors
                pass
        try:
            meters_site = client.get_json("/api/meters/site")
            cached = meters_site[0]["Cached_readings"]

            # --- voltages / powers / reactive powers (per phase) ---
            voltages = [self._safe_float(cached.get(f"v_l{phase}n")) for phase in range(1, 4)]
            p_list = [self._safe_float(cached.get(f"real_power_{ph}")) for ph in ["a", "b", "c"]]
            q_list = [self._safe_float(cached.get(f"reactive_power_{ph}")) for ph in ["a", "b", "c"]]

            # --- currents from API (often all 0 on Neurio/Tesla) ---
            api_currents = [self._safe_float(cached.get(f"i_{ph}_current")) for ph in ["a", "b", "c"]]

            # --- energy counters ---
            # IMPORTANT:
            # We use ONLY aggregate["site"]["energy_imported"/"energy_exported"] as the source for
            # imported/exported counters (same behaviour as the old/original module).
            #
            # We still *read* the per-phase energy fields (if available) ONLY for throttled diagnostic logging,
            # to see whether per-phase sums diverge from aggregate counters.
            def has_phase_energy(prefix: str) -> bool:
                return all((prefix + s) in cached for s in ["_a", "_b", "_c"])

            def sum_phase_energy_wh(prefix: str) -> float:
                # Keep as Wh (openWB uses Wh in many places; your logs match that)
                return (
                    self._safe_float(cached.get(prefix + "_a"))
                    + self._safe_float(cached.get(prefix + "_b"))
                    + self._safe_float(cached.get(prefix + "_c"))
                )

            imported = self._safe_float(aggregate["site"]["energy_imported"])
            exported = self._safe_float(aggregate["site"]["energy_exported"])

            # --- throttled diagnostics (1x per hour) ---
            # Log aggregate vs. per-phase sums to spot counter mismatches without affecting behaviour.
            now = time.time()
            if (now - self._last_energy_debug_log_ts) >= 3600:
                self._last_energy_debug_log_ts = now

                phase_imported = None
                phase_exported = None
                if has_phase_energy("energy_imported"):
                    phase_imported = sum_phase_energy_wh("energy_imported")
                if has_phase_energy("energy_exported"):
                    phase_exported = sum_phase_energy_wh("energy_exported")

                # These totals are present in Cached_readings too, but in some firmwares they can be absurd.
                cached_total_imported = cached.get("energy_imported")
                cached_total_exported = cached.get("energy_exported")

                # Deltas only make sense if units match; still useful to see large divergences.
                delta_imported = (phase_imported - imported) if phase_imported is not None else None
                delta_exported = (phase_exported - exported) if phase_exported is not None else None

                log.info(
                    "Powerwall energy debug (1h): aggregate_imported=%s aggregate_exported=%s "
                    "phase_sum_imported=%s phase_sum_exported=%s delta_imported=%s delta_exported=%s "
                    "cached_total_imported=%s cached_total_exported=%s",
                    imported,
                    exported,
                    phase_imported,
                    phase_exported,
                    delta_imported,
                    delta_exported,
                    cached_total_imported,
                    cached_total_exported,
                )

            # --- calculate PF + fallback currents if missing ---
            calculated_currents, power_factors = self._calc_currents_and_pf_from_pqu(
                voltages=voltages, p_list=p_list, q_list=q_list
            )

            # If all API currents are 0 -> use calculated currents
            if all(self._nearly_zero(i) for i in api_currents):
                currents = calculated_currents
                log.debug(
                    "Tesla/Neurio phase currents missing (all 0). Calculated currents from P/Q and U."
                )
            else:
                currents = api_currents
                # PF still useful even if currents exist
                log.debug("Using phase currents from Tesla/Neurio API.")

            powerwall_state = CounterState(
                imported=imported,
                exported=exported,
                power=self._safe_float(aggregate["site"]["instant_power"]),
                voltages=voltages,
                currents=currents,
                powers=p_list,
                power_factors=power_factors,
                frequency=int(round(self._safe_float(aggregate["site"].get("frequency", 50)))),
                serial_number=str(cached.get("serial_number", "")) if cached.get("serial_number") else "",
            )

        except (KeyError, HTTPError, IndexError, TypeError) as e:
            log.debug(
                "Firmware seems not to provide detailed phase measurements. Fallback to total power only. (%s)",
                str(e),
            )
            powerwall_state = CounterState(
                imported=self._safe_float(aggregate["site"]["energy_imported"]),
                exported=self._safe_float(aggregate["site"]["energy_exported"]),
                power=self._safe_float(aggregate["site"]["instant_power"]),
            )

        self.store.set(powerwall_state)


component_descriptor = ComponentDescriptor(configuration_factory=TeslaCounterSetup)

