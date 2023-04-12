import json
import re
from typing import Any


def get_index(topic: str) -> str:
    """extrahiert den Index aus einem Topic (Zahl zwischen zwei // oder am Stringende)
    """
    regex = re.search(r"\d", topic)
    if regex is None:
        raise Exception(f"Couldn't find index in {topic}")
    return regex.group()


def get_index_position(topic: str) -> int:
    regex = re.search(r"\d", topic)
    if regex is None:
        raise Exception(f"Couldn't find index in {topic}")
    return regex.start()


def get_second_index(topic: str) -> str:
    """extrahiert den zweiten Index aus einem Topic (Zahl zwischen zwei //)
    """
    regex = re.search('^.+/([0-9]*)/.+/([0-9]+)/*.*$', topic)
    if regex is None:
        raise Exception(f"Couldn't find index in {topic}")
    return regex.group(2)


def get_second_index_position(topic: str) -> int:
    regex = re.search('^.+/([0-9]*)/.+/([0-9]+)/*.*$', topic)
    if regex is None:
        raise Exception(f"Couldn't find index in {topic}")
    return regex.end(2)


def decode_payload(payload) -> Any:
    try:
        return json.loads(str(payload.decode("utf-8")))
    except (TypeError, json.decoder.JSONDecodeError):
        return str(payload.decode("utf-8"))
    except AttributeError:
        return payload
