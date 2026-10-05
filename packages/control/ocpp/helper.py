from datetime import datetime, timezone
import logging
from control import data

log = logging.getLogger(__name__)


def _get_formatted_time() -> str:
    return datetime.now(timezone.utc).isoformat()


def get_cp_from_chargebox_id(chargebox_id):
    for cp in data.data.cp_data.values():
        if cp.data.config.ocpp_chargebox_id == chargebox_id:
            return cp
    return None
