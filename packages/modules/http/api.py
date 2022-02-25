import functools
import logging
from typing import Callable, Union

from modules.common import req

log = logging.getLogger(__name__)


def request_value(url: str) -> float:
    if "none" == url:
        return 0
    else:
        response = req.get_http_session().get(url, timeout=5)
        response.encoding = 'utf-8'
        log.debug("Antwort auf "+str(url)+" "+str(response.text))
        return float(response.text.replace("\n", ""))


def create_request_function(domain: str, path: str) -> Callable[[], Union[int, float]]:
    if path == "none":
        return lambda: 0
    else:
        return functools.partial(request_value, domain + path)
