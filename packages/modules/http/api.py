import functools
import logging
from typing import Callable, Optional, Union

from modules.common import req

log = logging.getLogger(__name__)
soclog = logging.getLogger("soc."+__name__)


def _request_value(url: str) -> float:
    response_text = req.get_http_session().get(url, timeout=5).text
    log.debug("Antwort auf %s: %s", url, response_text)
    return float(response_text.replace("\n", ""))


def create_request_function(url: str, path: Optional[str]) -> Callable[[], float]:
    if path == "none" or path is None:
        return lambda: None
    else:
        return functools.partial(_request_value, url + path)


def fetch_soc(soc_url: str, range_url: str, vehicle: int) -> Union[int, float]:
    if soc_url is None or soc_url == "none":
        soclog.warn("http_soc: soc_url not defined - set soc to 0")
        soc = 0
    else:
        soc_text = req.get_http_session().get(soc_url, timeout=5).text
        soclog.debug("http_soc: soc_text="+soc_text)
        soc = int(soc_text)
    if range_url is None or range_url == "none":
        soclog.warn("http_soc: range_url not defined - set range to 0.0")
        range = float(0)
    else:
        range_text = req.get_http_session().get(range_url, timeout=5).text
        soclog.debug("http_soc: range_text="+range_text)
        range = float(range_text)
    soclog.info("http_soc: soc="+str(soc)+", range="+str(range))
    return soc, range
