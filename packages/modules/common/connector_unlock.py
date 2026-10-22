"""Local unlock handoff between the OCPP loop and the hardware handler."""
import asyncio
from concurrent.futures import Future
from dataclasses import dataclass, field
import math
from threading import Event, Lock
import time

UNLOCK_TIMEOUT = 25
UNLOCK_CURRENT_LIMIT = 0.2
UNLOCK_STABLE_SECONDS = 2.0


@dataclass
class UnlockRequest:
    deadline: float
    result: Future = field(default_factory=Future)
    cancelled: Event = field(default_factory=Event)


_requests = {}
_lock = Lock()


async def request_unlock(number: int) -> str:
    with _lock:
        previous = _requests.get(number)
        if previous is not None and not previous.result.done():
            return "failed"
        request = UnlockRequest(time.monotonic() + UNLOCK_TIMEOUT)
        _requests[number] = request
    try:
        return await asyncio.wait_for(asyncio.wrap_future(request.result), UNLOCK_TIMEOUT)
    except asyncio.TimeoutError:
        return "failed"
    finally:
        request.cancelled.set()
        request.result.cancel()


def take_unlock_request(number: int):
    """Claim a request once; expired/cancelled requests never reach hardware."""
    with _lock:
        request = _requests.get(number)
        if request is None or request.result.done() or request.result.running():
            return None
        if request.deadline <= time.monotonic():
            request.result.set_result("failed")
            return None
        if request.result.set_running_or_notify_cancel():
            return request
        return None


def currents_are_zero(currents) -> bool:
    return (isinstance(currents, (list, tuple)) and len(currents) == 3
            and all(type(value) in (int, float) and math.isfinite(value)
                    and abs(value) < UNLOCK_CURRENT_LIMIT for value in currents))
