from threading import Timer
import threading


class TimeoutException(Exception):
    pass


def exit_after(s):
    '''
    Nutze als Decorator, um einen Timeout für eine Funktion zu erzwingen.
    Wirft TimeoutException, wenn die Funktion länger als s Sekunden benötigt.
    Basiert auf https://stackoverflow.com/questions/492519/timeout-on-a-function-call.
    '''
    def outer(fn):
        def inner(*args, **kwargs):
            timer = Timer(
                s,
                lambda: thread_raise(TimeoutException(f"Timeout nach {s} Sekunden in {fn.__name__}")))
            timer.start()
            try:
                return fn(*args, **kwargs)
            finally:
                timer.cancel()
        return inner
    return outer


def thread_raise(ex):
    # Raise Exception im aktuellen Thread (nur für Hauptthread zuverlässig)
    import ctypes
    tid = threading.get_ident()
    ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_long(tid), ctypes.py_object(ex))
