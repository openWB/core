from dataclasses import dataclass, field
from threading import Event
from control.chargemode import Chargemode
from control.chargepoint.chargepoint_state import ChargepointState
from typing import Dict, List, Optional, Protocol, Union
from control.chargepoint.chargepoint_template import CpTemplate

from control.chargepoint.control_parameter import ControlParameter, control_parameter_factory
from control.ev.charge_template import ChargeTemplate
from control.ev.ev import Ev
from dataclass_utils.factories import currents_list_factory, empty_dict_factory, voltages_list_factory
from helpermodules.constants import DEFAULT_COLORS, NO_ERROR
from modules.chargepoints.openwb_pro.chargepoint_module import EvseSignaling
from modules.common.abstract_chargepoint import AbstractChargepoint


@dataclass
class ConnectedSoc:
    fault_str: str = NO_ERROR
    fault_state: int = 0
    range_charged: float = 0
    range_unit: str = "km"
    range: float = 0
    soc: int = 0
    timestamp: Optional[str] = None


@dataclass
class ConnectedSocConfig:
    configured: str = ""


@dataclass
class ConnectedInfo:
    id: int = 0
    name: str = "Ladepunkt"


@dataclass
class ConnectedConfig:
    average_consumption: float = 17
    charge_template: int = 0
    chargemode: Chargemode = Chargemode.STOP
    current_plan: Optional[int] = 0
    ev_template: int = 0
    time_charging_in_use: bool = False


def connected_config_factory() -> ConnectedConfig:
    return ConnectedConfig()


def connected_info_factory() -> ConnectedInfo:
    return ConnectedInfo()


def connected_soc_factory() -> ConnectedSoc:
    return ConnectedSoc()


@dataclass
class ConnectedVehicle:
    config: ConnectedConfig = field(default_factory=connected_config_factory,
                                    metadata={"topic": "get/connected_vehicle/config"})
    info: ConnectedInfo = field(default_factory=connected_info_factory,
                                metadata={"topic": "get/connected_vehicle/info"})
    soc: ConnectedSoc = field(default_factory=connected_soc_factory, metadata={"topic": "get/connected_vehicle/soc"})


OcppConfigKey = Dict[str, Union[bool, int, float, str]]


def ocpp_config_key_factory(
        value: Union[bool, int, float, str] = 0,
        readonly: bool = False,
        value_type: str = "int") -> OcppConfigKey:
    return {"value": value, "readonly": readonly, "type": value_type}


@dataclass
class OcppConfig:
    HeartbeatInterval: OcppConfigKey = field(
        default_factory=lambda: ocpp_config_key_factory(value=10, readonly=False, value_type="int")
    )
    MeterValueSampleInterval: OcppConfigKey = field(
        default_factory=lambda: ocpp_config_key_factory(value=20, readonly=False, value_type="int")
    )
    NumberOfConnectors: OcppConfigKey = field(
        default_factory=lambda: ocpp_config_key_factory(value=1, readonly=True, value_type="int")
    )
    SupportedFeatureProfiles: OcppConfigKey = field(
        default_factory=lambda: ocpp_config_key_factory(
            value="Core,RemoteTrigger", readonly=True, value_type="str"
        )
    )
    # Remote Reqest werden bei uns auch immer erst Authorize (siehe Remote_Start)
    AuthorizeRemoteTxRequests: OcppConfigKey = field(
        default_factory=lambda: ocpp_config_key_factory(value=True, readonly=True, value_type="bool")
    )

    MeterValuesSampledData: OcppConfigKey = field(
        default_factory=lambda: ocpp_config_key_factory(
            value="Energy.Active.Import.Register", readonly=True, value_type="str"
        )
    )
    TransactionMessageAttempts: OcppConfigKey = field(
        default_factory=lambda: ocpp_config_key_factory(value=3, readonly=False, value_type="int")
    )
    TransactionMessageRetryInterval: OcppConfigKey = field(
        default_factory=lambda: ocpp_config_key_factory(value=60, readonly=False, value_type="int")
    )


def ocpp_config_factory() -> OcppConfig:
    return OcppConfig()


def normalize_ocpp_connector_values(value: List[bool]) -> List[bool]:
    if not isinstance(value, list) or len(value) != 2 or not all(isinstance(item, bool) for item in value):
        raise ValueError("Expected two boolean connector values")
    return value.copy()


@dataclass
class Ocpp:
    connected: bool = False
    # Herkunft offener Vorgänge auch nach Backend-Neustart erhalten.
    last_connection_settings: Optional[Dict[str, str]] = None
    # neu erzeugte CPs sind per default erstmal available
    availability: List[bool] = field(default_factory=lambda: [True, True])
    transaction_id: Optional[int] = None
    # Bei ID-Wechsel alte Identität bis zum bestätigten Transaktionsende behalten.
    previous_chargebox_id: Optional[str] = None
    tag_accepted: bool = False
    remote_stop: bool = False
    unlock_stop: bool = False
    test_reconnect: bool = False
    # RFID/IdTag der laufenden OCPP-Transaction.
    transaction_id_tag: Optional[str] = None

    # Stop-Events, die während einer Offline-Phase aufgetreten sind.
    # Nach einem erfolgreichen Reconnect wird stop gesendet
    pending_transactions: list = field(default_factory=list,
                                       metadata={"topic": "get/ocpp/pending_transactions"})

    pending_availability: List[bool] = field(default_factory=lambda: [False, False])
    reset: bool = False

    # Status der Autorisierung und des Transaktionsstarts.
    authorization_flow_status: Optional[str] = None

    rfid_stop: bool = False

    config: OcppConfig = field(default_factory=ocpp_config_factory,
                               metadata={"topic": "get/ocpp/config"})


def empty_enery_source_dict_factory():
    return {'bat': 0, 'cp': 0, 'grid': 0, 'pv': 0}


@dataclass
class Log:
    chargemode_log_entry: str = "_"
    charged_energy_by_source: Dict[str, float] = field(default_factory=empty_enery_source_dict_factory)
    costs: float = 0
    end: Optional[float] = None
    exported_at_mode_switch: float = 0
    exported_at_plugtime: float = 0
    exported_since_mode_switch: float = 0
    exported_since_plugged: float = 0
    imported_at_mode_switch: float = 0
    imported_at_plugtime: float = 0
    imported_since_mode_switch: float = 0
    imported_since_plugged: float = 0
    range_charged: float = 0
    time_charged: float = 0
    timestamp_start_charging: Optional[float] = None
    timestamp_mode_switch: Optional[float] = None
    ev: int = -1
    prio: bool = False
    rfid: Optional[str] = None
    serial_number: Optional[str] = None
    soc_at_start: Optional[int] = None
    soc_at_end: Optional[int] = None
    range_at_start: Optional[float] = None
    range_at_end: Optional[float] = None
    odometer: Optional[float] = None


def connected_vehicle_factory() -> ConnectedVehicle:
    return ConnectedVehicle()


def ocpp_factory() -> Ocpp:
    return Ocpp()


@dataclass
class Get:
    charge_state: bool = False
    charging_current: Optional[float] = 0
    charging_power: Optional[float] = 0
    charging_voltage: Optional[float] = 0
    connected_vehicle: ConnectedVehicle = field(default_factory=connected_vehicle_factory)
    current_branch: Optional[str] = None
    current_commit: Optional[str] = None
    currents: List[float] = field(default_factory=currents_list_factory)
    daily_imported: float = field(default=0, metadata={"topic": "get/daily_imported"})
    daily_exported: float = field(default=0, metadata={"topic": "get/daily_exported"})
    error_code: Optional[int] = None
    error_timestamp: Optional[int] = None
    evse_current: Optional[float] = None
    # kann auch zur Laufzeit geändert werden
    evse_signaling: Optional[EvseSignaling] = None
    exported: float = 0
    fault_str: str = NO_ERROR
    fault_state: int = 0
    imported: float = 0
    max_charge_power: Optional[float] = None
    max_discharge_power: Optional[float] = None
    max_evse_current: Optional[int] = None
    ocpp: Ocpp = field(default_factory=ocpp_factory)
    phases_in_use: int = 0
    plug_state: bool = False
    power: float = 0
    powers: List[float] = field(default_factory=currents_list_factory)
    rfid_timestamp: Optional[float] = None
    rfid: Optional[int] = None
    serial_number: Optional[str] = None
    soc: Optional[float] = None
    soc_timestamp: Optional[int] = None
    state_str: Optional[str] = field(default=None, metadata={"topic": "get/state_str"})
    vehicle_id: Optional[str] = None
    version: Optional[str] = None
    voltages: List[float] = field(default_factory=voltages_list_factory)


def charge_template_factory() -> ChargeTemplate:
    return ChargeTemplate()


def ev_factory() -> Ev:
    return Ev(0)


def log_factory() -> Log:
    return Log()


@dataclass
class Set:
    charge_template: ChargeTemplate = field(default_factory=charge_template_factory)
    current: float = field(default=0, metadata={"topic": "set/current"})
    ev_prev: int = field(default=0, metadata={"topic": "set/ev_prev"})
    log: Log = field(default_factory=log_factory, metadata={"topic": "set/log"})
    manual_lock: bool = field(default=False, metadata={"topic": "set/manual_lock"})
    phases_to_use: int = field(default=0, metadata={"topic": "set/phases_to_use"})
    plug_state_prev: bool = field(default=False, metadata={"topic": "set/plug_state_prev"})
    plug_time: Optional[float] = field(default=None, metadata={"topic": "set/plug_time"})
    required_power: float = field(default=0, metadata={"topic": "set/required_power"})
    rfid: Optional[str] = field(default=None, metadata={"topic": "set/rfid"})
    # set current aus dem vorherigen Zyklus, um zu wissen, ob am Ende des Zyklus die Ladung freigegeben wird
    # (für Control-Pilot-Unterbrechung)
    current_prev: float = field(default=0.0, metadata={"topic": "set/current_prev"})
    target_current: float = field(default=0)  # Zwischenergebnis vom Algorithmus
    charging_ev_data: Ev = field(default_factory=ev_factory)
    charge_state_prev: bool = field(default=False, metadata={"topic": "set/charge_state_prev"})
    # control_parameter.state aus dem vorherigen Zyklus, um eine Control-Pilot-Unterbrechung beim
    # Ladestart von einer, die direkt nach einer echten Phasenumschaltung erfolgt, zu unterscheiden
    # (siehe initiate_control_pilot_interruption()).
    state_prev: ChargepointState = field(default=ChargepointState.NO_CHARGING_ALLOWED,
                                         metadata={"topic": "set/state_prev"})
    # letzter CP-SoC-Timestamp, für den bereits ein force_soc_update ausgelöst wurde, und das zugehörige EV,
    # um bei dauerhaft veraltetem EV-SoC (zB API-Fehler) nicht jeden Zyklus erneut ein Update anzustoßen,
    # aber bei einem EV-Wechsel am selben Ladepunkt trotzdem einmal neu auszulösen
    soc_timestamp_force_update_prev: Optional[int] = field(
        default=None, metadata={"topic": "set/soc_timestamp_force_update_prev"})
    soc_timestamp_force_update_prev_ev: Optional[int] = field(
        default=None, metadata={"topic": "set/soc_timestamp_force_update_prev_ev"})


@dataclass
class Config:
    configuration: Dict = field(default_factory=empty_dict_factory)
    _ev: int = 0
    name: str = "neuer Ladepunkt"
    color: str = DEFAULT_COLORS.CHARGEPOINT.value
    type: Optional[str] = None
    template: int = 0
    connected_phases: int = 3
    phase_1: int = 1
    auto_phase_switch_hw: bool = False
    control_pilot_interruption_hw: bool = False
    id: int = 0
    ocpp_chargebox_id: Optional[str] = None
    ocpp_chargebox_password: Optional[str] = None

    def __post_init__(self):
        self.event_update_state: Event

    @property
    def ev(self) -> int:
        return self._ev

    @ev.setter
    def ev(self, ev: int):
        self._ev = ev
        try:
            self.event_update_state.set()
        except AttributeError:
            pass

    def __getstate__(self):
        state = self.__dict__.copy()
        if state.get('event_update_state'):
            del state['event_update_state']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)


def get_factory() -> Get:
    return Get()


def set_factory() -> Set:
    return Set()


def config_factory() -> Config:
    return Config()


@dataclass
class ChargepointData:
    control_parameter: ControlParameter = field(default_factory=control_parameter_factory)
    get: Get = field(default_factory=get_factory)
    set: Set = field(default_factory=set_factory)
    config: Config = field(default_factory=config_factory, metadata={"topic": "config"})

    def set_event(self, event: Optional[Event] = None) -> None:
        self.event_update_state = event
        if event:
            self.config.event_update_state = event

    def __getstate__(self):
        # Copy the object's state from self.__dict__ which contains
        # all our instance attributes. Always use the dict.copy()
        # method to avoid modifying the original state.
        state = self.__dict__.copy()
        # Remove the unpicklable entries.
        if state.get('event_update_state'):
            del state['event_update_state']
        return state

    def __setstate__(self, state):
        # Restore instance attributes (i.e., filename and lineno).
        self.__dict__.update(state)


class ChargepointProtocol(Protocol):
    @property
    def template(self) -> CpTemplate: ...
    @property
    def chargepoint_module(self) -> AbstractChargepoint: ...
    @property
    def num(self) -> int: ...
    @property
    def data(self) -> ChargepointData: ...
