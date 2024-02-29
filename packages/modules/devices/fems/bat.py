import logging
from requests import Session
from helpermodules.scale_metric import scale_metric
from modules.devices.fems.config import FemsBatSetup
from modules.common.component_state import BatState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_bat_value_store
from modules.devices.fems.version import FemsVersion, get_version
log = logging.getLogger(__name__)


class FemsBat:
    def __init__(self, ip_address: str, component_config: FemsBatSetup, session: Session) -> None:
        self.ip_address = ip_address
        self.component_config = component_config
        self.session = session
        self.store = get_bat_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        if self.component_config.configuration.num == 1:
            self._data = "ess0"
        else:
            self._data = "ess2"
        self.version = get_version(self.get_data_by_multiple_segement_regex_query)
        log.debug(f"{self.component_config.name} unterstützt {self.version.value}")

    def get_data_by_multiple_segement_regex_query(self):
        return self.session.get(
            (f"http://{self.ip_address}:8084/rest/channel/({self._data}|_sum)/"
             "(Soc|DcChargeEnergy|DcDischargeEnergy|GridActivePower|ProductionActivePower|ConsumptionActivePower)"),
            timeout=2).json()

    def update(self) -> None:
        if self.version == FemsVersion.MULTIPLE_SEGMENT_REGEX_QUERY:
            response = self.get_data_by_multiple_segement_regex_query()
            for singleValue in response:
                address = singleValue["address"]
                if (address == self._data+"/Soc"):
                    soc = singleValue["value"]
                elif address == self._data+"/DcChargeEnergy":
                    imported = scale_metric(singleValue['value'], singleValue.get('unit'), 'Wh')
                elif address == self._data+"/DcDischargeEnergy":
                    exported = scale_metric(singleValue['value'], singleValue.get('unit'), 'Wh')
                elif address == "_sum/GridActivePower":
                    grid = scale_metric(singleValue['value'], singleValue.get('unit'), 'W')
                elif address == "_sum/ProductionActivePower":
                    pv = scale_metric(singleValue['value'], singleValue.get('unit'), 'W')
                elif address == "_sum/ConsumptionActivePower":
                    haus = scale_metric(singleValue['value'], singleValue.get('unit'), 'W')
        else:
            response = self.session.get(
                f"http://{self.ip_address}:8084/rest/channel/{self._data}/(Soc|DcChargeEnergy|DcDischargeEnergy)",
                timeout=2).json()
            for singleValue in response:
                address = singleValue["address"]
                if (address == self._data+"/Soc"):
                    soc = singleValue["value"]
                elif address == self._data+"/DcChargeEnergy":
                    imported = scale_metric(singleValue['value'], singleValue.get('unit'), 'Wh')
                elif address == self._data+"/DcDischargeEnergy":
                    exported = scale_metric(singleValue['value'], singleValue.get('unit'), 'Wh')
                elif address == "_sum/GridActivePower":
                    grid = scale_metric(singleValue['value'], singleValue.get('unit'), 'W')

            response = self.session.get(
                (f"http://{self.ip_address}:8084/rest/channel/_sum/(GridActivePower|ProductionActivePower|"
                 "ConsumptionActivePower)"),
                timeout=2).json()
            for singleValue in response:
                address = singleValue["address"]
                if (address == "_sum/GridActivePower"):
                    grid = scale_metric(singleValue['value'], singleValue.get('unit'), 'W')
                elif address == "_sum/ProductionActivePower":
                    pv = scale_metric(singleValue['value'], singleValue.get('unit'), 'W')
                elif address == "_sum/ConsumptionActivePower":
                    haus = scale_metric(singleValue['value'], singleValue.get('unit'), 'W')
        # keine Berechnung im Gerät, da grid nicht der Leistung aus der Zählerkomponente entspricht.
        power = grid + pv - haus
        bat_state = BatState(
            power=power,
            soc=soc,
            imported=imported,
            exported=exported
        )
        self.store.set(bat_state)


component_descriptor = ComponentDescriptor(configuration_factory=FemsBatSetup)
