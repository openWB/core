import copy
import logging
from requests import Response, Session
import urllib3
from functools import wraps
import warnings

log = logging.getLogger(__name__)


def disable_insecure_request_warning(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if kwargs.get('verify') is False:
            # store the original filters to restore them after the request
            original_filters = warnings.filters[:]
            # disable the warning for this request
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            try:
                return func(*args, **kwargs)
            finally:
                # restore the original filters
                warnings.filters = original_filters
        else:
            return func(*args, **kwargs)
    return wrapper


class CustomSession(Session):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_timeout = 5

    @disable_insecure_request_warning
    def request(self, method, url, *args, **kwargs):
        kwargs.setdefault('timeout', self.default_timeout)
        return super().request(method, url, *args, **kwargs)

    def __deepcopy__(self, memo):
        """die deepcopy-methode von python kopiert keine Klassenattribute, daher wird hier eine eigene deepcopy-Methode
        implementiert"""
        new_copy = self.__class__()
        new_copy.default_timeout = self.default_timeout
        for k, v in self.__dict__.items():
            if k != 'default_timeout':
                setattr(new_copy, k, copy.deepcopy(v, memo))
        return new_copy


def _log_response(response: Response, *args, **kwargs) -> None:
    if not log.isEnabledFor(logging.DEBUG):
        return
    content_type = response.headers.get('Content-Type', '').split(';', 1)[0].strip().lower()
    binary = (content_type.startswith(('image/', 'audio/', 'video/', 'font/')) or
              content_type in ('application/zip', 'application/x-zip-compressed',
                               'application/octet-stream', 'application/pdf', 'application/gzip'))
    # The portal can omit/mislabel the content type of ZIP downloads.
    if binary or response.content.startswith((b'PK\x03\x04', b'PK\x05\x06', b'PK\x07\x08')):
        log.debug("Get-Response: binary data (%s, %s bytes)", content_type or 'unknown type', len(response.content))
    else:
        log.debug("Get-Response: %s", response.text)


def get_http_session() -> CustomSession:
    session = CustomSession()
    session.hooks['response'].append(lambda r, *args, **kwargs: r.raise_for_status())
    session.hooks['response'].append(_log_response)
    return session
