import logging
from threading import Thread, enumerate
import time
from typing import List, Optional

log = logging.getLogger(__name__)


def joined_thread_handler(threads: List[Thread], timeout: Optional[int]) -> List[str]:
    def split_chunks(to_split, n):
        for i in range(0, len(to_split), n):
            yield to_split[i:i + n]

    not_finished_threads = []
    threads_splitted = list(split_chunks(threads, 50))

    for threads_chunk in threads_splitted:
        threads_to_keep = []

        for thread in threads_chunk:
            if is_thread_alive(thread.name):
                log.error(f"{thread.name} ist bereits aktiv und wird nicht erneut gestartet.")
                not_finished_threads.append(thread.name)
            else:
                threads_to_keep.append(thread)
        # Start them all
        for thread in threads_to_keep:
            thread.start()

        if threads_to_keep:
            if timeout is not None:
                start_time = time.monotonic()
                while time.monotonic() - start_time < timeout:
                    if not [t for t in threads_to_keep if t.is_alive()]:
                        break
                    time.sleep(0.05)
            else:
                for thread in threads_to_keep:
                    thread.join()

        for thread in threads_to_keep:
            if thread.is_alive():
                log.error(f"{thread.name} konnte nicht innerhalb des Timeouts abgearbeitet werden.")
                not_finished_threads.append(thread.name)
    # Entferne alle beendeten Threads aus der übergebenen Liste
    threads[:] = [t for t in threads if t.is_alive()]
    return not_finished_threads


def thread_handler(thread: Thread) -> bool:
    if is_thread_alive(thread.name):
        log.error(f"Thread {thread.name} ist bereits aktiv und wird nicht erneut gestartet.")
        return False
    else:
        thread.start()
        return True


def is_thread_alive(thread_name: str) -> bool:
    return any(running_thread.name == thread_name for running_thread in enumerate())
