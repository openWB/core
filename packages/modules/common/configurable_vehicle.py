from enum import Enum
import logging
import time
from typing import Optional, TypeVar, Generic, Callable
from helpermodules import timecheck

from helpermodules.pub import Pub
from dataclass_utils import asdict
from modules.common import store
from modules.common.abstract_vehicle import CalculatedSocState, GeneralVehicleConfig, VehicleUpdateData
from modules.common.abstract_vehicle import VehicleFallbackData
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import CarState
from modules.common.fault_state import ComponentInfo, FaultState
from modules.vehicles.common.calc_soc import calc_soc
from modules.vehicles.manual.config import ManualSoc
from modules.vehicles.mqtt.config import MqttSocSetup
from control import data


T_VEHICLE_CONFIG = TypeVar("T_VEHICLE_CONFIG")

log = logging.getLogger(__name__)


def get_CarName(vehicle: int) -> str:
    for ev in data.data.ev_data.values():
        if int(ev.num) == int(vehicle):
            _name = ev.data.name
            break
    else:
        _name = "Unknown"
    return _name


class SocSource(Enum):
    API = "api"
    CP = "chargepoint"
    MANUAL = "manual"
    CALCULATION = "calculation"
    NO_UPDATE = "no_update"


class ConfigurableVehicle(Generic[T_VEHICLE_CONFIG]):
    def __init__(self,
                 vehicle_config: T_VEHICLE_CONFIG,
                 component_updater: Callable[[VehicleUpdateData], CarState],
                 vehicle: int,
                 calc_while_charging: bool = False,
                 general_config: Optional[GeneralVehicleConfig] = None,
                 calculated_soc_state: Optional[CalculatedSocState] = None,
                 initializer: Callable = lambda: None) -> None:
        self.__component_updater = component_updater
        self.vehicle_config = vehicle_config
        self.calculated_soc_state = calculated_soc_state
        self.__initializer = initializer
        if calculated_soc_state is None:
            self.calculated_soc_state = CalculatedSocState()
        else:
            self.calculated_soc_state = calculated_soc_state
        self.general_config = general_config
        if general_config is None:
            self.general_config = GeneralVehicleConfig()
        else:
            self.general_config = general_config
        self.calc_while_charging = calc_while_charging
        self.vehicle = vehicle
        self.store = store.get_car_value_store(self.vehicle)
        self.fault_state = FaultState(ComponentInfo(self.vehicle, self.vehicle_config.name, "vehicle"))
        # nach Init auf NO_ERROR setzen, damit der Fehlerstatus beim Modulwechsel gelöscht wird
        self.fault_state.no_error()
        self.fault_state.store_error()

        try:
            self.__initializer()
        except Exception:
            log.exception(f"Initialisierung von Fahrzeug {self.vehicle_config.name} fehlgeschlagen")

    def update(self, vehicle_update_data: VehicleUpdateData):
        log.debug(f"Vehicle Instance {type(self.vehicle_config)}")
        log.debug(f"Calculated SoC-State {self.calculated_soc_state}")
        log.debug(f"Vehicle Update Data {vehicle_update_data}")
        log.debug(f"General Config {self.general_config}")
        with SingleComponentUpdateContext(self.fault_state, self.__initializer):

            if vehicle_update_data.imported is None:
                self.calculated_soc_state.last_imported = None
                Pub().pub(f"openWB/set/vehicle/{self.vehicle}/soc_module/calculated_soc_state",
                          asdict(self.calculated_soc_state))
            source = self._get_carstate_source(vehicle_update_data)
            if source == SocSource.NO_UPDATE:
                log.debug("No soc update necessary.")
                return
            car_state = self._get_carstate_by_source(vehicle_update_data, source)
            if isinstance(self.vehicle_config, MqttSocSetup) and car_state is None:
                log.debug("Mqtt uses legacy topics.")
                return
            log.debug(f"Requested start soc from {source.value}: {car_state.soc}%")
            if (vehicle_update_data.last_soc_timestamp is None or
                    vehicle_update_data.last_soc_timestamp <= car_state.soc_timestamp + 60):
                # Nur wenn der SoC neuer ist als der bisherige, diesen setzen.
                # Manche Fahrzeuge liefern in Ladepausen zwar einen SoC, aber manchmal einen alten.
                # Die Pro liefert manchmal den SoC nicht, bis nach dem Anstecken das SoC-Update getriggert wird.
                # Wenn Sie dann doch noch den alten SoC liefert, darf dieser nicht verworfen werden.
                self.store.set(car_state)
            else:
                log.debug("Not updating SoC, because timestamp is older.")
            self.calculated_soc_state.last_imported = vehicle_update_data.imported
            Pub().pub(f"openWB/set/vehicle/{self.vehicle}/soc_module/calculated_soc_state",
                      asdict(self.calculated_soc_state))

    def _get_carstate_source(self, vehicle_update_data: VehicleUpdateData) -> SocSource:
        # Kein SoC vom LP vorhanden oder erwünscht
        if (vehicle_update_data.soc_from_cp is None or self.general_config.use_soc_from_cp is False or
                # oder aktueller manueller SoC vorhanden (ausgelesenen SoC während der Ladung korrigieren)
                self.calculated_soc_state.manual_soc is not None):
            if isinstance(self.vehicle_config, ManualSoc):
                # Wenn ein manueller SoC gesetzt wurde, diesen als neuen Start merken.
                if self.calculated_soc_state.manual_soc is not None:
                    return SocSource.MANUAL
                else:
                    if vehicle_update_data.plug_state:
                        return SocSource.CALCULATION
                    else:
                        # Wenn nicht angesteckt ist, nichts berechnen.
                        return SocSource.NO_UPDATE
            else:
                if vehicle_update_data.charge_state and self.calc_while_charging:
                    # Wenn während dem Laden berechnet werden soll und gerade geladen wird, berechnen.
                    return SocSource.CALCULATION
                else:
                    return SocSource.API
        else:
            if self._is_soc_timestamp_valid(vehicle_update_data):
                return SocSource.CP
            else:
                # Wenn SoC vom LP nicht mehr aktuell, dann berechnen.
                return SocSource.CALCULATION

    def _get_carstate_by_source(self, vehicle_update_data: VehicleUpdateData, source: SocSource) -> CarState:
        # global variables used for fallback calculation
        global vfbd

        _v = self.vehicle  # vehicle id
        if 'vfbd' not in globals():
            vfbd = {}
        if _v not in vfbd:
            vfbd[_v] = VehicleFallbackData(get_CarName(_v))

        _log = f"carstate: entry: carName: {vfbd[_v].carName}/{self.vehicle_config.name},"
        _log += f" last_soc_timestamp: {vfbd[_v].last_soc_timestamp}"
        log.debug(_log)
        if source == SocSource.API:
            try:
                # check for plug_state from False to True and remember timestamp
                if vehicle_update_data.plug_state and not vfbd[_v].last_plug_state:
                    vfbd[_v].last_plugin_timestamp = time.time()
                vfbd[_v].last_plug_state = vehicle_update_data.plug_state
                _carState = self.__component_updater(vehicle_update_data)
                if self.vehicle_config.name == "MQTT":
                    return _carState
                if _carState.soc <= 0:
                    try_calc = True
                    log.debug("carstate: API exception")
                else:
                    try_calc = False
                    vfbd[_v].last_soc_timestamp = time.time()
                    log.debug(f"carstate: API successful, last_soc_timestamp: {vfbd[_v].last_soc_timestamp}")
                log.debug(f"carstate: return: last_soc_timestamp: {vfbd[_v].last_soc_timestamp}")
                return _carState
            except Exception:
                log.info(f"SoC-Auslesung von Fahrzeug {vfbd[_v].carName} fehlgeschlagen")
                _carState = CarState(0, 0.0)
                try_calc = True
                log.debug("carstate: API exception")
            if _carState:
                if try_calc and\
                  _carState.soc <= 0 and\
                   vehicle_update_data.plug_state and\
                   vehicle_update_data.last_soc and\
                   vfbd[_v].last_soc_timestamp >= vfbd[_v].last_plugin_timestamp and\
                   (self.calculated_soc_state.last_imported or vehicle_update_data.imported):
                    log.info(f"SoC FALLBACK: SoC von Fahrzeug {vfbd[_v].carName} wird berechnet")
                    _carState = CarState(soc=calc_soc.calc_soc(
                                         vehicle_update_data,
                                         vehicle_update_data.efficiency,
                                         self.calculated_soc_state.last_imported or vehicle_update_data.imported,
                                         vehicle_update_data.battery_capacity))
                else:
                    log.info(f"SoC FALLBACK: SoC von Fahrzeug {vfbd[_v].carName} kann nicht berechnet werden")
                    log.debug(f"try_calc: {try_calc}, _carState.soc: {_carState.soc}")
                    log.debug(f"plug_state: {vehicle_update_data.plug_state}")
                    log.debug(f"last_soc: {vehicle_update_data.last_soc}")
                    log.debug(f"last_soc_timestamp: {vfbd[_v].last_soc_timestamp}")
                    _check = vfbd[_v].last_soc_timestamp >= vfbd[_v].last_plugin_timestamp
                    log.debug(f"timestamp-check: {_check}")
                    log.debug(f"last_plugin_timestamp: {vfbd[_v].last_plugin_timestamp}")
                    log.debug(f"self.calculated_soc_state.last_imported: {self.calculated_soc_state.last_imported}")
                    log.debug(f"vehicle_update_data.imported: {vehicle_update_data.imported}")
                    _ex = f"SoC von Fahrzeug {vfbd[_v].carName} kann weder ausgelesen noch berechnet werden"
                    raise Exception(_ex)
            return _carState
        elif source == SocSource.CALCULATION:
            return CarState(soc=calc_soc.calc_soc(
                vehicle_update_data,
                vehicle_update_data.efficiency,
                self.calculated_soc_state.last_imported or vehicle_update_data.imported,
                vehicle_update_data.battery_capacity))
        elif source == SocSource.CP:
            return CarState(soc=vehicle_update_data.soc_from_cp,
                            soc_timestamp=vehicle_update_data.timestamp_soc_from_cp)
        elif source == SocSource.MANUAL:
            if self.calculated_soc_state.manual_soc is not None:
                soc = self.calculated_soc_state.manual_soc
            else:
                raise ValueError("Manual soc source selected, but no manual soc set.")
            self.calculated_soc_state.manual_soc = None
            return CarState(soc)

    def _is_soc_timestamp_valid(self, vehicle_update_data: VehicleUpdateData) -> bool:
        if vehicle_update_data.timestamp_soc_from_cp:
            soc_ts = vehicle_update_data.timestamp_soc_from_cp + 60
            now_ts = timecheck.create_timestamp()
            return soc_ts > now_ts
        else:
            return False
