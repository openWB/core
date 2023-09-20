import logging
from typing import Optional, TypeVar, Generic, Callable

from helpermodules.pub import Pub
from dataclass_utils import asdict
from modules.common import store
from modules.common.abstract_vehicle import GeneralVehicleConfig, VehicleUpdateData
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import CarState
from modules.common.fault_state import ComponentInfo
from modules.vehicles.common.calc_soc.calc_soc import calc_soc
from modules.vehicles.manual.config import ManualSoc

T_VEHICLE_CONFIG = TypeVar("T_VEHICLE_CONFIG")

log = logging.getLogger(__name__)


class ConfigurableVehicle(Generic[T_VEHICLE_CONFIG]):
    def __init__(self,
                 vehicle_config: T_VEHICLE_CONFIG,
                 component_updater: Callable[[VehicleUpdateData], CarState],
                 vehicle: int,
                 calc_while_charging: bool = False,
                 general_config: Optional[GeneralVehicleConfig] = None) -> None:
        self.__component_updater = component_updater
        self.vehicle_config = vehicle_config
        self.general_config = general_config
        if general_config is None:
            self.general_config = GeneralVehicleConfig()
        else:
            self.general_config = general_config
        self.calc_while_charging = calc_while_charging
        self.vehicle = vehicle
        self.store = store.get_car_value_store(self.vehicle)
        self.component_info = ComponentInfo(self.vehicle, self.vehicle_config.name, "vehicle")

    def update(self, vehicle_update_data: VehicleUpdateData):
        with SingleComponentUpdateContext(self.component_info):
            if (self.calc_while_charging or
                    self.general_config.use_soc_from_cp or
                    isinstance(self.vehicle_config, ManualSoc)):
                if self.general_config.request_start_soc or vehicle_update_data.plug_state is False:
                    # Nur wenn angesteckt ist, kann ein initialer SoC abgefragt werden.
                    if vehicle_update_data.soc_from_cp is None or self.general_config.manual_soc:
                        if isinstance(self.vehicle_config, ManualSoc):
                            soc = self.general_config.manual_soc
                            self.general_config.manual_soc = None
                            source_str = "manual"
                        else:
                            soc = self.__component_updater(vehicle_update_data)
                            source_str = "api"
                    else:
                        soc = vehicle_update_data.soc_from_cp
                        source_str = "chargepoint"
                    log.debug(f"Requested start soc from {source_str}: {soc}%")
                    self.general_config.soc_start = soc

                    # Flag zurücksetzen, dass ein initialer SoC als Berechnungsgrundlage gesetzt werden soll:
                    # - bei Berechnung während Ladung (zB PSA): SoC immer vom Server abfragen, wenn nicht geladen wird
                    # - bei Auslesen aus Auto: Initialen SoC setzen, wenn neu angesteckt wurde
                    if ((self.calc_while_charging and vehicle_update_data.charge_state is False) or
                            (self.general_config.use_soc_from_cp and vehicle_update_data.plug_state is False)):
                        self.general_config.request_start_soc = True
                        self.general_config.soc_start = None
                    else:
                        self.general_config.request_start_soc = False
                    self.general_config.imported_start = vehicle_update_data.imported
                    Pub().pub(f"openWB/set/vehicle/{self.vehicle}/soc_module/general_config",
                              asdict(self.general_config))
                else:
                    soc = calc_soc(vehicle_update_data,
                                   self.general_config.efficiency,
                                   self.general_config.imported_start,
                                   self.general_config.soc_start,
                                   vehicle_update_data.battery_capacity)
                self.store.set(CarState(soc))
            else:
                self.store.set(self.__component_updater(vehicle_update_data))
