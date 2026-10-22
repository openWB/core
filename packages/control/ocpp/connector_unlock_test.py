import asyncio
from threading import Thread
import time

import pytest

from modules.common import connector_unlock as unlock


@pytest.fixture(autouse=True)
def local_requests(monkeypatch):
    monkeypatch.setattr(unlock, "_requests", {})


def test_local_result_crosses_threads_and_request_can_only_be_claimed_once():
    async def run():
        task = asyncio.create_task(unlock.request_unlock(0))
        await asyncio.sleep(0)
        request = unlock.take_unlock_request(0)
        assert request is not None
        assert unlock.take_unlock_request(0) is None
        thread = Thread(target=request.result.set_result, args=("unlocked",))
        thread.start()
        assert await task == "unlocked"
        thread.join()
        assert unlock.take_unlock_request(0) is None
    asyncio.run(run())


def test_second_request_is_rejected_while_hardware_owns_first():
    async def run():
        task = asyncio.create_task(unlock.request_unlock(0))
        await asyncio.sleep(0)
        request = unlock.take_unlock_request(0)
        assert await unlock.request_unlock(0) == "failed"
        request.result.set_result("unlocked")
        assert await task == "unlocked"
    asyncio.run(run())


def test_cancelled_pending_request_never_reaches_hardware():
    async def run():
        task = asyncio.create_task(unlock.request_unlock(0))
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert unlock.take_unlock_request(0) is None
    asyncio.run(run())


def test_cancellation_signals_running_hardware_and_keeps_it_exclusive():
    async def run():
        task = asyncio.create_task(unlock.request_unlock(0))
        await asyncio.sleep(0)
        request = unlock.take_unlock_request(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert request.cancelled.is_set()
        assert await unlock.request_unlock(0) == "failed"
        request.result.set_result("failed")
    asyncio.run(run())


def test_timeout_discards_unclaimed_request(monkeypatch):
    monkeypatch.setattr(unlock, "UNLOCK_TIMEOUT", 0.01)
    assert asyncio.run(unlock.request_unlock(0)) == "failed"
    assert unlock.take_unlock_request(0) is None


def test_expired_request_is_failed_without_claiming():
    request = unlock.UnlockRequest(time.monotonic() - 1)
    unlock._requests[0] = request
    assert unlock.take_unlock_request(0) is None
    assert request.result.result() == "failed"
