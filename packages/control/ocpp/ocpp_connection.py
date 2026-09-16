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
