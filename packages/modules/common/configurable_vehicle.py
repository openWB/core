from enum import Enum
import logging
from typing import Optional, TypeVar, Generic, Callable
from helpermodules import timecheck

from helpermodules.pub import Pub
from dataclass_utils import asdict
from modules.common import store
from modules.common.abstract_vehicle import CalculatedSocState, GeneralVehicleConfig, VehicleUpdateData
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import CarState
from modules.common.fault_state import ComponentInfo, FaultState
from modules.vehicles.common.calc_soc import calc_soc
from modules.vehicles.manual.config import ManualSoc
from modules.vehicles.mqtt.config import MqttSocSetup

T_VEHICLE_CONFIG = TypeVar("T_VEHICLE_CONFIG")

log = logging.getLogger(__name__)


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
                 calculated_soc_state: Optional[CalculatedSocState] = None) -> None:
        self.__component_updater = component_updater
        self.vehicle_config = vehicle_config
        self.calculated_soc_state = calculated_soc_state
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

    def update(self, vehicle_update_data: VehicleUpdateData):
        log.debug(f"Vehicle Instance {type(self.vehicle_config)}")
        log.debug(f"Calculated SoC-State {self.calculated_soc_state}")
        log.debug(f"Vehicle Update Data {vehicle_update_data}")
        log.debug(f"General Config {self.general_config}")
        with SingleComponentUpdateContext(self.fault_state):

            source = self._get_carstate_source(vehicle_update_data)
            if source == SocSource.NO_UPDATE:
                log.debug("No soc update necessary.")
                return
            car_state = self._get_carstate_by_source(vehicle_update_data, source)
            log.debug(f"Requested start soc from {source.value}: {car_state.soc}%")

            if (source != SocSource.CALCULATION or
                    (vehicle_update_data.imported and self.calculated_soc_state.imported_start is None)):
                # Wenn nicht berechnet wurde, SoC als Start merken.
                self.calculated_soc_state.imported_start = vehicle_update_data.imported
                self.calculated_soc_state.soc_start = car_state.soc
                Pub().pub(f"openWB/set/vehicle/{self.vehicle}/soc_module/calculated_soc_state",
                          asdict(self.calculated_soc_state))
            if vehicle_update_data.soc_timestamp is None or vehicle_update_data.soc_timestamp < car_state.soc_timestamp:
                # Nur wenn der SoC neuer ist als der bisherige, diesen setzen.
                self.store.set(car_state)
            else:
                log.debug("Not updating SoC, because timestamp is older.")

    def _get_carstate_source(self, vehicle_update_data: VehicleUpdateData) -> SocSource:
        if isinstance(self.vehicle_config, MqttSocSetup):
            return SocSource.NO_UPDATE
        # Kein SoC vom LP vorhanden oder erwünscht
        if (vehicle_update_data.soc_from_cp is None or self.general_config.use_soc_from_cp is False or
                # oder aktueller manueller SoC vorhanden (ausgelesenen SoC während der Ladung korrigieren)
                self.calculated_soc_state.manual_soc):
            if isinstance(self.vehicle_config, ManualSoc):
                # Wenn ein manueller SoC gesetzt wurde, diesen als neuen Start merken.
                if self.calculated_soc_state.manual_soc or self.calculated_soc_state.imported_start is None:
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
        if source == SocSource.API:
            return self.__component_updater(vehicle_update_data)
        elif source == SocSource.CALCULATION:
            return CarState(soc=calc_soc.calc_soc(
                vehicle_update_data,
                vehicle_update_data.efficiency,
                self.calculated_soc_state.imported_start or vehicle_update_data.imported,
                self.calculated_soc_state.soc_start,
                vehicle_update_data.battery_capacity))
        elif source == SocSource.CP:
            return CarState(soc=vehicle_update_data.soc_from_cp,
                            soc_timestamp=vehicle_update_data.timestamp_soc_from_cp)
        elif source == SocSource.MANUAL:
            soc = self.calculated_soc_state.manual_soc or self.calculated_soc_state.soc_start
            self.calculated_soc_state.manual_soc = None
            return CarState(soc)

    def _is_soc_timestamp_valid(self, vehicle_update_data: VehicleUpdateData) -> bool:
        if vehicle_update_data.timestamp_soc_from_cp:
            soc_ts = vehicle_update_data.timestamp_soc_from_cp + 60
            now_ts = timecheck.create_timestamp()
            return soc_ts > now_ts
        else:
            return False
