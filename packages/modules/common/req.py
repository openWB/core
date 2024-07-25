
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


def get_http_session() -> CustomSession:
    session = CustomSession()
    session.hooks['response'].append(lambda r, *args, **kwargs: r.raise_for_status())
    session.hooks['response'].append(lambda r, *args, **kwargs: log.debug("Get-Response: " + r.text))
    return session
