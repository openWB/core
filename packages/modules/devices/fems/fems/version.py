from enum import Enum

import requests


class FemsVersion(Enum):
    SINGLE_SEGMENT_REGEX_QUERY = "multiple segment regey queries"
    MULTIPLE_SEGMENT_REGEX_QUERY = "single segment regey queries"


def get_version(multiple_segement_regex_query_func):
    try:
        multiple_segement_regex_query_func()
        return FemsVersion.MULTIPLE_SEGMENT_REGEX_QUERY
    # FEMS, die Regex-Abfragen über mehrere Segmente unterstützen, dürfen nicht zu häufig abgefragt werden.
    # Alle Werte müssen auf einmal abgefragt werden.
    except requests.exceptions.HTTPError:
        return FemsVersion.SINGLE_SEGMENT_REGEX_QUERY
