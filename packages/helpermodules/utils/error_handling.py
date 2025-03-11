import logging
import time

from helpermodules import timecheck
from helpermodules.messaging import MessageType
from helpermodules.pub import Pub


log = logging.getLogger(__name__)

CP_ERROR = ("Anhaltender Fehler beim Auslesen des Ladepunkts. Soll-Stromstärke, Lade- und Stecker-Status wird "
            "zurückgesetzt.")


class ErrorTimerContext:
    def __init__(self, topic: str, exceeded_msg: str, timeout: int = 60, hide_exception: bool = False):
        self.topic = topic
        self.timeout = timeout
        self.hide_exception = hide_exception
        self.error_timestamp = None
        self.__exceeded_msg = exceeded_msg

    def __enter__(self):
        return None

    def __exit__(self, exception_type, exception, exception_traceback) -> bool:
        if exception:
            if self.error_timestamp is None:
                self.error_timestamp = timecheck.create_timestamp()
                Pub().pub(self.topic, self.error_timestamp)
            log.error(exception)
            if self.hide_exception is False or timecheck.check_timestamp(self.error_timestamp, self.timeout) is False:
                return False
        return True

    def error_counter_exceeded(self) -> bool:
        if self.error_timestamp and timecheck.check_timestamp(self.error_timestamp, self.timeout) is False:
            log.error(self.__exceeded_msg)
            return True
        else:
            return False

    def reset_error_counter(self):
        self.error_timestamp = None
        Pub().pub(self.topic, self.error_timestamp)


class ImportErrorContext:
    def __init__(self):
        pass

    def __enter__(self):
        return None

    def __exit__(self, exception_type, exception, exception_traceback) -> bool:
        if isinstance(exception, ModuleNotFoundError):
            try:
                msg = ("Importfehler: Das Python-Modul " + exception.args[0].split("'")[1] + " wurde nicht gefunden." +
                       " Bitte sicherstellen, dass diese openWB eine Verbindung zum Internet besitzt. Beim nächsten " +
                       "Neustart wird versucht, fehlende Software-Pakete zu installieren.")
            except IndexError:
                msg = "Importfehler: " + str(exception)
            # pub_system_message() publlished an openWB/set/, dass wird beim Starten gelöscht
            log.exception(msg)
            now = time.time()
            message_payload = {
                "source": "command",
                "type": MessageType.ERROR.value,
                "message": msg,
                "timestamp": int(now)
            }
            Pub().pub(f'openWB/system/messages/{(now * 1000):.0f}', message_payload)
        return True
