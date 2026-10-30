from typing import Dict, List, Optional

from modules.common.component_state import ConsumerState, CounterState


class TasmotaParser:
    """Read only the requested measurements from a Status 8 or Status 0 response."""

    def __init__(self, response: Dict, phase: int = 1) -> None:
        self.phase = phase
        self.relay_status = response.get('Status', {})
        self.meter_type: Optional[str] = None
        self.meter: Dict = {}
        status = response.get('StatusSNS', {})
        for meter_type in ('ENERGY', 'Itron', 'MT681', 'eBZ', 'MT631'):
            if meter_type in status:
                self.meter_type = meter_type
                self.meter = status[meter_type]
                break
        else:
            if 'Power' in self.relay_status:
                return
            raise ValueError("Nicht unterstützter Tasmota Zählertyp. Bitte an den Support wenden.")

    def _phase_values(self, key: str, attribute: str) -> List[float]:
        values = getattr(CounterState(), attribute)
        if self.meter_type == 'ENERGY' and self.meter.get(key) is not None:
            values[self.phase-1] = float(self.meter[key])
        return values

    @property
    def currents(self) -> List[float]:
        return self._phase_values('Current', 'currents')

    @property
    def exported(self) -> float:
        if self.meter_type == 'ENERGY':
            return CounterState().exported
        if self.meter_type == 'MT681':
            key = 'Total_out'
        elif self.meter_type == 'Itron' and 'E_in' not in self.meter:
            key = 'ExportActive'
        else:
            key = 'E_out'
        return float(self.meter[key]) * 1000 if self.meter.get(key) is not None else CounterState().exported

    @property
    def imported(self) -> float:
        if self.meter_type == 'ENERGY':
            key = 'Total'
        elif self.meter_type == 'MT681':
            key = 'Total_in'
        elif self.meter_type == 'Itron' and 'E_in' not in self.meter:
            key = 'ImportActive'
        else:
            key = 'E_in'
        return float(self.meter[key]) * 1000 if self.meter.get(key) is not None else CounterState().imported

    @property
    def power(self) -> float:
        key = 'Watt_summe' if self.meter_type == 'MT681' else 'Power'
        return float(self.meter[key]) if self.meter.get(key) is not None else CounterState().power

    @property
    def power_factors(self) -> List[float]:
        return self._phase_values('Factor', 'power_factors')

    @property
    def powers(self) -> List[float]:
        if self.meter_type == 'ENERGY':
            return self._phase_values('Power', 'powers')
        values = CounterState().powers
        if self.meter_type == 'eBZ':
            keys = ('36_7_0', '56_7_0', '76_7_0')
            for index, key in enumerate(keys):
                if self.meter.get(key) is not None:
                    values[index] = float(self.meter[key])
        return values

    @property
    def state(self) -> bool:
        if self.relay_status.get('Power') is not None:
            return bool(self.relay_status['Power'])
        return ConsumerState().state

    @property
    def voltages(self) -> List[float]:
        return self._phase_values('Voltage', 'voltages')
