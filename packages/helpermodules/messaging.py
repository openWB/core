from enum import Enum
import logging
import time
from typing import Optional
from helpermodules.pub import Pub

log = logging.getLogger(__name__)


class MessageType(Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "danger"


class MessageTarget(Enum):
    SYSTEM = 0
    USER = 1


def pub_user_message(payload: dict, connection_id: str, message: str,
                     message_type: MessageType = MessageType.INFO) -> None:
    """ sendet eine Meldung an den Benutzer
    """
    _pub_message(payload, connection_id, message, message_type, MessageTarget.USER)


def pub_system_message(payload: dict, message: str,
                       message_type: MessageType = MessageType.INFO) -> None:
    """ sendet eine Meldung an den Benutzer
    """
    _pub_message(payload, None, message, message_type, MessageTarget.SYSTEM)


def _pub_message(payload: dict, connection_id: Optional[str], message: str,
                 message_type: MessageType = MessageType.INFO,
                 message_target: MessageTarget = MessageTarget.USER) -> None:
    """ sendet eine Meldung
    """
    try:
        log.debug(f'pub_message: message: \'{message}\' type: \'{message_type}\' target: \'{message_target}\'')
        now = time.time()
        message_payload = {
            "source": "command",
            "type": message_type.value,
            "message": message,
            "timestamp": int(now)
        }
        # default to system message
        topic = f'openWB/system/messages/{(now * 1000):.0f}'
        if message_target == MessageTarget.USER:
            # if connection_id is empty, send as system message
            if connection_id is not None:
                topic = f'openWB/set/command/{connection_id}/messages/{(now * 1000):.0f}'
            else:
                log.warning('Benutzerbenachrichtigung ohne \'connection_id\'')
        Pub().pub(topic, message_payload)
        if message_type == MessageType.ERROR:
            log.error(f'Befehl konnte nicht ausgeführt werden: {message_payload}')
        else:
            log.debug(f'Befehl erfolgreich ausgeführt: {message}')
    except Exception:
        log.exception("Fehler im Command-Modul")


def pub_error_global(payload: dict, connection_id: str, error_str: str) -> None:
    """ sendet ein Fehler-Topic, warum der Befehl nicht ausgeführt werden konnte.
    """
    try:
        error_payload = {
            "command": payload["command"],
            "data": payload["data"],
            "error": error_str
        }
        Pub().pub(f'openWB/set/command/{connection_id}/error', error_payload)
        log.error(f'Befehl konnte nicht ausgeführt werden: {error_payload}')
    except Exception:
        log.exception("Fehler im Command-Modul")
