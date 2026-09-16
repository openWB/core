import logging
log = logging.getLogger(__name__)


class OcppConnection:

    def __init__(
        self,
        chargebox_id,
        ws,
        cp,
    ):
        self.chargebox_id = chargebox_id
        self.ws = ws
        self.cp = cp

        self.start_task = None
        self.heartbeat_task = None
        self.meter_task = None

        self.boot_accepted = False
        self.closing = False
