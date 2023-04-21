from typing import Optional, Tuple, Union, List
import logging

from dataclass_utils import dataclass_from_dict
from helpermodules.cli import run_using_positional_cli_args
from modules.common import req
from modules.common import store
from modules.common.abstract_device import DeviceDescriptor
from modules.common.abstract_soc import AbstractSoc, SocUpdateData
from modules.common.component_context import SingleComponentUpdateContext
from modules.common.component_state import CarState
from modules.common.fault_state import ComponentInfo
from modules.vehicles.http.config import HttpSocSetup, HttpSocConfiguration


log = logging.getLogger(__name__)


class Soc(AbstractSoc):
    def __init__(self, device_config: Union[dict, HttpSocSetup], vehicle: int):
        self.config = dataclass_from_dict(HttpSocSetup, device_config)
        self.vehicle = vehicle
        self.store = store.get_car_value_store(self.vehicle)
        self.component_info = ComponentInfo(self.vehicle, self.config.name, "vehicle")

    def update(self, soc_update_data: SocUpdateData) -> None:
        with SingleComponentUpdateContext(self.component_info):
            soc, range = self._fetch_soc(
                self.config.configuration.soc_url,
                self.config.configuration.range_url)
            self.store.set(CarState(soc, range))

    def _fetch_soc(self, soc_url: Optional[str], range_url: Optional[str]) -> Tuple[int, float]:
        if soc_url is None or soc_url == "none":
            log.warn("http_soc: soc_url not defined - set soc to 0")
            soc = 0
        else:
            soc_text = req.get_http_session().get(soc_url, timeout=5).text
            soc = int(soc_text)
        if range_url is None or range_url == "none":
            log.warn("http_soc: range_url not defined - set range to 0.0")
            range = float(0)
        else:
            range_text = req.get_http_session().get(range_url, timeout=5).text
            range = float(range_text)
        log.info("http_soc: soc="+str(soc)+", range="+str(range))
        return soc, range


def http_update(soc_url: str, range_url: str, charge_point: int):
    log.debug("http_soc: soc_url="+soc_url+"range_url="+range_url+"charge_point="+str(charge_point))
    Soc(HttpSocSetup(configuration=HttpSocConfiguration(soc_url, range_url)),
        charge_point).update(SocUpdateData())


def main(argv: List[str]):
    run_using_positional_cli_args(http_update, argv)


device_descriptor = DeviceDescriptor(configuration_factory=HttpSocSetup)
