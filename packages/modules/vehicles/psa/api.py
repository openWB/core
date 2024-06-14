#!/usr/bin/env python3

import logging
from modules.common.component_state import CarState

from modules.vehicles.psa.config import PSAConfiguration

log = logging.getLogger(__name__)


def fetch_soc(config: PSAConfiguration,
              vehicle_id: int) -> CarState:
    raise Exception("Dieses Modul ist nicht mehr funktionstüchtig. Bitte auf anderen Anbeiter, z.b. Tronity, wechseln.")
