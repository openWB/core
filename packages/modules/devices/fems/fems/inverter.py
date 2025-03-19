import logging
from requests import Session
from helpermodules.scale_metric import scale_metric
from modules.devices.fems.fems.config import FemsInverterSetup
from modules.common.abstract_device import AbstractInverter
from modules.common.component_state import InverterState
from modules.common.component_type import ComponentDescriptor
from modules.common.fault_state import ComponentInfo, FaultState
from modules.common.store import get_inverter_value_store
from modules.devices.fems.fems.version import FemsVersion, get_version
log = logging.getLogger(__name__)


class FemsInverter(AbstractInverter):
    def __init__(self, ip_address: str, component_config: FemsInverterSetup, session: Session) -> None:
        self.ip_address = ip_address
        self.component_config = component_config
        self.session = session
        self.store = get_inverter_value_store(self.component_config.id)
        self.fault_state = FaultState(ComponentInfo.from_component_config(self.component_config))
        self.version = get_version(self.get_data_by_multiple_segement_regex_query)
        log.debug(f"{self.component_config.name} unterstützt {self.version.value}")

    def get_data_by_multiple_segement_regex_query(self):
        return self.session.get(
            'http://'+self.ip_address+':8084/rest/channel/_sum/(ProductionActivePower|ProductionActiveEnergy)',
            timeout=2).json()

    def update(self) -> None:
        if self.version == FemsVersion.MULTIPLE_SEGMENT_REGEX_QUERY:
            response = self.get_data_by_multiple_segement_regex_query()
            for singleValue in response:
                address = singleValue["address"]
                if address == "_sum/ProductionActivePower":
                    power = scale_metric(singleValue['value'], singleValue.get('unit'), 'W') * -1
                elif address == "_sum/ProductionActiveEnergy":
                    exported = scale_metric(singleValue['value'], singleValue.get('unit'), 'Wh')
        else:
            response = self.session.get(
                'http://'+self.ip_address+':8084/rest/channel/_sum/ProductionActivePower',
                timeout=2).json()
            power = scale_metric(response["value"], response.get("unit"), 'W') * -1
            response = self.session.get(
                'http://'+self.ip_address+':8084/rest/channel/_sum/ProductionActiveEnergy',
                timeout=2).json()
            exported = scale_metric(response["value"], response.get("unit"), 'Wh')
        inverter_state = InverterState(
            power=power,
            exported=exported
        )
        self.store.set(inverter_state)


component_descriptor = ComponentDescriptor(configuration_factory=FemsInverterSetup)
