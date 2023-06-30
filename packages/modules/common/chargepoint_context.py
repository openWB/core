from modules.internal_chargepoint_handler.clients import ClientHandler


class HardwareCheckContext:
    def __init__(self, client: ClientHandler):
        self.client = client

    def __enter__(self):
        return None

    def __exit__(self, exception_type, exception, exception_traceback) -> bool:
        if exception:
            self.client.check_hardware()
            raise exception
        return True
