import re


def get_index(topic: str) -> str:
    """extrahiert den Index aus einem Topic (Zahl zwischen zwei // oder am Stringende)
    """
    regex = re.search('(?!/)([0-9]*)(?=/|$)', topic)
    if regex is None:
        raise Exception(f"Couldn't find index in {topic}")
    return regex.group()


def get_second_index(topic: str) -> str:
    """extrahiert den zweiten Index aus einem Topic (Zahl zwischen zwei //)
    """
    regex = re.search('^.+/([0-9]*)/.+/([0-9]+)/*.*$', topic)
    if regex is None:
        raise Exception(f"Couldn't find index in {topic}")
    return regex.group(2)
