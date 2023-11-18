"""YourCharge Daten
"""
from dataclasses import dataclass, field
import logging
import random
from typing import List, Optional

from control import data
from helpermodules import hardware_configuration
from helpermodules.pub import Pub
from helpermodules import timecheck
from modules import ripple_control_receiver

log = logging.getLogger(__name__)


@dataclass
class YcConfig:
    active: bool = False

def yc_config_factory() -> YcConfig:
    return YcConfig()


@dataclass
class YcData:
    yc_config: YcConfig = field(default_factory=yc_config_factory)


class YourCharge:
    """Config and data for use by YourCharge charge system algorithms
    """

    def __init__(self):
        self.data: YcData = YcData()
