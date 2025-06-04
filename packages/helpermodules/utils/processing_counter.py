from threading import Event, Lock


class ProcessingCounter:
    def __init__(self, done_event: Event):
        self.lock = Lock()
        self.counter = 0
        self.done_event = done_event

    def add_task(self):
        with self.lock:
            self.counter += 1
            self.done_event.clear()

    def task_done(self):
        with self.lock:
            self.counter -= 1
            if self.counter <= 0:
                self.done_event.set()

    def wait_for_completion(self, timeout=None):
        return self.done_event.wait(timeout)

    def is_done(self):
        with self.lock:
            return self.counter == 0
