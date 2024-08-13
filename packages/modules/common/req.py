
import copy
import logging
from requests import Session

log = logging.getLogger(__name__)


class CustomSession(Session):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.default_timeout = 5

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


def get_http_session() -> CustomSession:
    session = CustomSession()
    session.hooks['response'].append(lambda r, *args, **kwargs: r.raise_for_status())
    session.hooks['response'].append(lambda r, *args, **kwargs: log.debug("Get-Response: " + r.text))
    return session
