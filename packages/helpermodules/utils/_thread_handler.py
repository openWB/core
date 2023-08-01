import logging
import threading
from typing import List, Optional

log = logging.getLogger(__name__)


def thread_handler(threads: List[threading.Thread], timeout: Optional[int]) -> List[str]:
    def split_chunks(to_split, n):
        for i in range(0, len(to_split), n):
            yield to_split[i:i + n]

    not_finished_threads = []
    threads_splitted = list(split_chunks(threads, 50))
    for threads_chunk in threads_splitted:
        # Start them all
        for thread in threads_chunk:
            thread.start()

        # Wait for all to complete
        for thread in threads_chunk:
            thread.join(timeout=timeout)

        for thread in threads_chunk:
            if thread.is_alive():
                log.error(f"{thread.name} konnte nicht innerhalb des Timeouts die Werte abfragen, die abgefragten "
                          "Werte werden nicht in der Regelung verwendet.")
                not_finished_threads.append(thread.name)
    return not_finished_threads
