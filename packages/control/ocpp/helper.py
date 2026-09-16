from datetime import datetime, timezone
import logging
from control import data
from modules.common.fault_state import FaultState

log = logging.getLogger(__name__)


def _get_formatted_time() -> str:
    return datetime.now(timezone.utc).isoformat()
