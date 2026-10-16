#!/usr/bin/env python3
import logging
import math

from requests import HTTPError

from modules.common.abstract_device import AbstractCounter
from modules.common.component_state import CounterState
from modules.common.component_type import ComponentDescriptor, ComponentType
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_component_value_store
from modules.common.utils.peak_filter import PeakFilter
from modules.devices.tesla.tesla.config import TeslaCounterSetup
from modules.devices.tesla.tesla.http_client import PowerwallHttpClient

log = logging.getLogger(__name__)


class TeslaCounter(AbstractCounter):
    def __init__(self, component_config: TeslaCounterSetup) -> None:
        self.component_config = component_config
        # Powerwall 3 / newer gateway firmware no longer provide /api/meters/site (HTTP 404).
        # Remember that, so we do not request the endpoint again in every cycle.
        self._meters_site_available = True

    def initialize(self) -> None:
        self.store = get_component_value_store(
            self.component_config.type,
            self.component_config.id,
        )
        self.fault_state = FaultState(
            ComponentInfo.from_component_config(self.component_config)
        )
        self.peak_filter = PeakFilter(ComponentType.COUNTER, self.component_config.id, self.fault_state)

    @staticmethod
    def _nearly_zero(x: float, eps: float = 1e-9) -> bool:
        return abs(x) < eps

    def _calc_currents_and_pf_from_pqu(
        self,
        voltages: list[float],
        p_list: list[float],
        q_list: list[float],
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
            u = voltages[i]
            p = p_list[i]
            q = q_list[i]

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

    def _get_meters_site(self, client: PowerwallHttpClient):
        if not self._meters_site_available:
            return None
        try:
            return client.get_json("/api/meters/site")
        except HTTPError as e:
            status = getattr(getattr(e, "response", None), "status_code", None)
            if status != 404:
                raise
            self._meters_site_available = False
            log.info(
                "Tesla gateway does not provide /api/meters/site (HTTP 404, e.g. Powerwall 3). "
                "Using total values from /api/meters/aggregates only."
            )
            return None

    def update(self, client: PowerwallHttpClient, aggregate):
        site = aggregate["site"]
        power = site["instant_power"]
        imported, exported = self.peak_filter.check_values(
            power, site["energy_imported"], site["energy_exported"])

        try:
            meters_site = self._get_meters_site(client)
            if meters_site is None:
                raise KeyError("/api/meters/site not available")
            cached = meters_site[0]["Cached_readings"]

            voltages = [
                float(cached[f"v_l{phase}n"])
                for phase in range(1, 4)
            ]

            p_list = [
                float(cached[f"real_power_{phase}"])
                for phase in ["a", "b", "c"]
            ]

            q_list = [
                float(cached[f"reactive_power_{phase}"])
                for phase in ["a", "b", "c"]
            ]

            api_currents = [
                float(cached[f"i_{phase}_current"])
                for phase in ["a", "b", "c"]
            ]

            calculated_currents, power_factors = (
                self._calc_currents_and_pf_from_pqu(
                    voltages=voltages,
                    p_list=p_list,
                    q_list=q_list,
                )
            )

            if all(self._nearly_zero(i) for i in api_currents):
                currents = calculated_currents
                log.debug(
                    "Tesla/Neurio phase currents missing (all 0). "
                    "Calculated currents locally from P/Q and U."
                )
            else:
                currents = api_currents
                log.debug(
                    "Using phase currents from Tesla/Neurio API."
                )

            frequency = float(site["frequency"])

            serial = cached.get("serial_number")
            serial_number = str(serial) if serial else None

            powerwall_state = CounterState(
                imported=imported,
                exported=exported,
                power=power,
                voltages=voltages,
                currents=currents,
                powers=p_list,
                power_factors=power_factors,
                frequency=round(frequency, 2),
                serial_number=serial_number,
            )

        except (KeyError, IndexError, TypeError, ValueError) as e:
            log.debug(
                "Firmware seems not to provide detailed phase measurements. "
                "Fallback to total power only. (%s)",
                str(e),
            )

            powerwall_state = CounterState(
                imported=imported,
                exported=exported,
                power=power,
            )

        self.store.set(powerwall_state)


component_descriptor = ComponentDescriptor(
    configuration_factory=TeslaCounterSetup
)
