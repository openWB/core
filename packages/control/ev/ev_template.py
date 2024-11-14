from dataclasses import dataclass, field


@dataclass
class EvTemplateData:
    dc_min_current: int = 0
    dc_max_current: int = 0
    name: str = "Fahrzeug-Profil"
    max_current_multi_phases: int = 16
    max_phases: int = 3
    phase_switch_pause: int = 2
    prevent_phase_switch: bool = False
    prevent_charge_stop: bool = False
    control_pilot_interruption: bool = False
    control_pilot_interruption_duration: int = 4
    average_consump: float = 17000
    min_current: int = 6
    max_current_single_phase: int = 16
    battery_capacity: float = 82000
    efficiency: float = 90
    nominal_difference: float = 1
    keep_charge_active_duration: int = 40


def ev_template_data_factory() -> EvTemplateData:
    return EvTemplateData()


@dataclass
class EvTemplate:
    """ Klasse mit den EV-Daten
    """

    data: EvTemplateData = field(default_factory=ev_template_data_factory, metadata={
                                 "topic": "config"})
    et_num: int = 0
