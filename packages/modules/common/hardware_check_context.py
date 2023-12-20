from modules.internal_chargepoint_handler.clients import ClientHandler


class SeriesHardwareCheckContext:
    def __init__(self, client: ClientHandler):
        self.client = client

    def __enter__(self):
        self.client.check_hardware()
        return None

    def __exit__(self, exception_type, exception, exception_traceback) -> bool:
        return True
