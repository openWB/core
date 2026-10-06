
from control.ocpp.ocpp_chargepoint import OcppChargePoint
import logging
from enum import Enum

log = logging.getLogger(__name__)


class RegistrationState(str, Enum):
    PENDING = "Pending"
    ACCEPTED = "Accepted"
    REJECTED = "Rejected"


class OcppConnection:

    def __init__(
        self,
        chargebox_id,
        ws,
        cp: OcppChargePoint,
    ):
        self.chargebox_id = chargebox_id
        self.ws = ws
        self.cp = cp

        self.start_task = None
        self.heartbeat_task = None
        self.meter_task = None
        self.retry_task = None

        self.registration_state = None
        self.retry_interval = None
        self.boot_accepted = False
        self.closing = False
