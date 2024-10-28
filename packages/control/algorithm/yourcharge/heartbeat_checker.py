import logging
import datetime

from control import data

log = logging.getLogger(__name__)


class HeartbeatChecker:
    def __init__(self, timeout: datetime.timedelta = datetime.timedelta(seconds=30)) -> None:
        self.heartbeat_timeout = timeout
        self._timeout_detection_time = None
        self._previous_lcs_publish = -1
        self._timeout_reported = False

    def is_heartbeat_ok(self) -> bool:

        now_it_is = datetime.datetime.now(datetime.timezone.utc)

        log.debug(f"LCS heartbeat ENTER: now it is {now_it_is}, last_controller_publish="
                  + f"{data.data.yc_data.data.last_controller_publish}, _previous_lcs_publish="
                  + f"{self._previous_lcs_publish}, _timeout_detection_time={self._timeout_detection_time}")

        if self._previous_lcs_publish == -1:
            # very first run: just store the last_controller_publish
            log.debug(f"LCS heartbeat initialized to: {data.data.yc_data.data.last_controller_publish}")
            self._previous_lcs_publish = data.data.yc_data.data.last_controller_publish
            self._timeout_detection_time = now_it_is - self.heartbeat_timeout
            return False

        if self._previous_lcs_publish == data.data.yc_data.data.last_controller_publish:
            # no new controller timestamp seen
            if self._timeout_detection_time is None:
                # first time no change --> start timeout timer
                log.error(f"No LCS heartbeat change (first time): now it is {now_it_is}, "
                          + f"last_controller_publish={data.data.yc_data.data.last_controller_publish}")
                self._timeout_detection_time = now_it_is
                self._timeout_reported = False
            else:
                timeout_since = now_it_is - self._timeout_detection_time
                log.debug(f"LCS heartbeat DETECTED: now it is {now_it_is}, last_controller_publish="
                          + f"{data.data.yc_data.data.last_controller_publish}, _previous_lcs_publish="
                          + f"{self._previous_lcs_publish}, _timeout_detection_time={self._timeout_detection_time}")
                if timeout_since > self.heartbeat_timeout:
                    # timeout detected
                    if not self._timeout_reported:
                        log.critical(f"LCS heartbeat ERROR: now it is {now_it_is}, timeout_detection_time="
                                     + f"{self._timeout_detection_time} --> timeout since {timeout_since} > "
                                     + f"heartbeat_timeout ({self.heartbeat_timeout})")
                        self._timeout_reported = True
                    return False
        else:
            self._previous_lcs_publish = data.data.yc_data.data.last_controller_publish
            if self._timeout_detection_time is not None:
                log.critical(f"LCS heartbeat returned: now it is {now_it_is}, last_controller_publish="
                             + f"{data.data.yc_data.data.last_controller_publish}")
                self._timeout_detection_time = None
                self._timeout_reported = False

        log.debug(f"LCS heartbeat OK: now it is {now_it_is}, last_controller_publish="
                  + f"{data.data.yc_data.data.last_controller_publish}, _previous_lcs_publish="
                  + f"{self._previous_lcs_publish}, _timeout_detection_time={self._timeout_detection_time}")

        return True
