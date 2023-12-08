import logging

from datetime import datetime, timedelta
from control import data

log = logging.getLogger(__name__)

class HeartbeatChecker:
    def __init__(self, timeout: timedelta = timedelta(seconds=30)) -> None:
        self.heartbeat_timeout = timeout
        self._timeout_detection_time = None
        self._previous_lcs_publish = -1

    def is_heartbeat_timeout(self) -> bool:

        now_it_is = datetime.utcnow()

        log.info(f"LCS heartbeat ENTER: now it is {now_it_is}, last_controller_publish={data.data.yc_data.data.last_controller_publish}, _previous_lcs_publish={self._previous_lcs_publish}, _timeout_detection_time={self._timeout_detection_time}")

        if self._previous_lcs_publish == -1:
            # very first run: just store the last_controller_publish
            log.info(f"LCS heartbeat initialized to: {data.data.yc_data.data.last_controller_publish}")
            self._previous_lcs_publish = data.data.yc_data.data.last_controller_publish
            return True

        if self._previous_lcs_publish == data.data.yc_data.data.last_controller_publish:
            # no new controller timestamp seen
            if self._timeout_detection_time == None:
                # first time no change --> start timeout timer
                log.warning(f"No LCS heartbeat change (first time): now it is {now_it_is}, last_controller_publish={data.data.yc_data.data.last_controller_publish}")
                self._timeout_detection_time = now_it_is
            else:
                timeout_since = now_it_is - self._timeout_detection_time
                log.info(f"LCS heartbeat DETECTED: now it is {now_it_is}, last_controller_publish={data.data.yc_data.data.last_controller_publish}, _previous_lcs_publish={self._previous_lcs_publish}, _timeout_detection_time={self._timeout_detection_time}")
                if timeout_since > self.heartbeat_timeout:
                    # timeout detected
                    log.critical(f"LCS heartbeat ERROR: now it is {now_it_is}, timeout_detection_time={self._timeout_detection_time} --> timeout since {timeout_since} > heartbeat_timeout ({self.heartbeat_timeout})")
                    return False

        elif self._timeout_detection_time != None:
            log.warning(f"LCS heartbeat returned: now it is {now_it_is}, last_controller_publish={data.data.yc_data.data.last_controller_publish}")
            self._timeout_detection_time = None

        log.info(f"LCS heartbeat OK: now it is {now_it_is}, last_controller_publish={data.data.yc_data.data.last_controller_publish}, _previous_lcs_publish={self._previous_lcs_publish}, _timeout_detection_time={self._timeout_detection_time}")

        return True
