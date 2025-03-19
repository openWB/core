import logging
import threading
from typing import List, Optional

log = logging.getLogger(__name__)


def joined_thread_handler(threads: List[threading.Thread], timeout: Optional[int]) -> List[str]:
    def split_chunks(to_split, n):
        for i in range(0, len(to_split), n):
            yield to_split[i:i + n]

    not_finished_threads = []
    threads_splitted = list(split_chunks(threads, 50))

    for threads_chunk in threads_splitted:
        for thread in threads_chunk:
            if is_thread_alive(thread.name):
                log.error(f"{thread.name} ist bereits aktiv und wird nicht erneut gestartet.")
                not_finished_threads.append(thread.name)
                threads_chunk.remove(thread)
                break
        # Start them all
        for thread in threads_chunk:
            thread.start()

        # Wait for all to complete
        for thread in threads_chunk:
            thread.join(timeout=timeout)

        for thread in threads_chunk:
            if thread.is_alive():
                log.error(f"{thread.name} konnte nicht innerhalb des Timeouts abgearbeitet werden.")
                not_finished_threads.append(thread.name)
    return not_finished_threads


def thread_handler(thread: threading.Thread) -> bool:
    if is_thread_alive(thread.name):
        log.error(f"Thread {thread.name} ist bereits aktiv und wird nicht erneut gestartet.")
        return False
    else:
        thread.start()
        return True


def is_thread_alive(thread_name: str) -> bool:
    return any(running_thread.name == thread_name for running_thread in threading.enumerate())
