#!/usr/bin/env python3
import logging
import math
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
          - I = S / U (signed via P)
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

            s = math.sqrt(p * p + q * q)

            if self._nearly_zero(s):
                currents[i] = 0.0
                pfs[i] = 0.0
                continue

            pfs[i] = p / s
            i_mag = s / u
            currents[i] = i_mag if p >= 0 else -i_mag

        return currents, pfs

    def update(self, client: PowerwallHttpClient, aggregate):
							   
														   
																			 
						   
													
							  
													 
							  

					   
				
																		
															   
															  
							 
																			
					

        try:
            meters_site = client.get_json("/api/meters/site")
            cached = meters_site[0]["Cached_readings"]

            # --- voltages / powers / reactive powers (per phase) ---
            voltages = [self._safe_float(cached.get(f"v_l{phase}n")) for phase in range(1, 4)]
            p_list = [self._safe_float(cached.get(f"real_power_{ph}")) for ph in ["a", "b", "c"]]
            q_list = [self._safe_float(cached.get(f"reactive_power_{ph}")) for ph in ["a", "b", "c"]]

            # --- currents from API (often all 0 on Neurio/Tesla) ---
            api_currents = [self._safe_float(cached.get(f"i_{ph}_current")) for ph in ["a", "b", "c"]]

            # --- energy counters: use aggregate site values as sole source ---
            imported = self._safe_float(aggregate["site"]["energy_imported"])
            exported = self._safe_float(aggregate["site"]["energy_exported"])

            # --- local fallback for Tesla/Neurio setups with missing phase currents ---
            calculated_currents, power_factors = self._calc_currents_and_pf_from_pqu(
                voltages=voltages,
                p_list=p_list,
                q_list=q_list,
            )

						
            if all(self._nearly_zero(i) for i in api_currents):
                currents = calculated_currents
                log.debug(
                    "Tesla/Neurio phase currents missing (all 0). "
                    "Calculated currents locally from P/Q and U."
                )
            else:
                currents = api_currents
                log.debug("Using phase currents from Tesla/Neurio API.")

            freq = self._safe_float(aggregate["site"].get("frequency", 50.0), 50.0)

            serial = cached.get("serial_number")
            serial_number = str(serial) if serial else None

            powerwall_state = CounterState(
                imported=imported,
                exported=exported,
                power=self._safe_float(aggregate["site"]["instant_power"]),
                voltages=voltages,
                currents=currents,
                powers=p_list,
                power_factors=power_factors,
                frequency=round(freq, 2),
                serial_number=serial_number,
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
