import logging

from datetime import datetime, timedelta

from control import data, yourcharge
from control.algorithm import algorithm

from helpermodules.pub import Pub

log = logging.getLogger(__name__)


class AlgorithmYc(algorithm.Algorithm):

    yc_root_topic = 'yourCharge'
    yc_status_topic = yc_root_topic + '/status'

    def __init__(self):
        super().__init__()
        (key, value) = next(((key, value) for i, (key, value) in enumerate(data.data.cp_data.items()) if value.chargepoint_module.config.type == 'internal_openwb'), None)
        self._internal_cp = value
        self._internal_cp_key = key
        self._heartbeat_checker = HeartbeatChecker(timedelta(seconds=25))
        self._heartbeat_status = None
        self._previous_heartbeat_status = None
        self._lm_status = None
        self._previous_lm_status = None
        log.info(f"YC algorithm active: Internal CP found with key '{self._internal_cp_key}'")

    def calc_current(self) -> None:

        try:
            self._heartbeat_status = self._heartbeat_checker.is_heartbeat_timeout()

            # super-early exit in case of controller not being seen anymore, charge current --> 0
            if self._heartbeat_status == False:
                log.critical(f"Detected controller heartbeat timeout: Disabling charge immediately")
                self._internal_cp.data.set.current = 0
                self._lm_status = yourcharge.LmStatus.DownByError
                return

            # very early exit in case of box being administratively disabled
            if data.data.yc_data.data.yc_config.active != True:
                log.info(f"Box is administratively disabled: Disabling charge immediately")
                self._internal_cp.data.set.current = 0
                self._lm_status = yourcharge.LmStatus.DownByDisable
                return

            # handle supersede or regular control
            if data.data.yc_data.data.yc_control.fixed_charge_current is None:
                log.info(f"Regular load control requested by yc_data.data.yc_control.fixed_charge_current == {data.data.yc_data.datayc_control.fixed_charge_current}")
                self.do_load_control()
            else:
                # handling of superseded, fixed charge current
                if data.data.yc_data.data.yc_control.fixed_charge_current < 0.0:
                    # invalid or default value < 0.0
                    log.info(f"Charging disapproved by yc_data.data.yc_control.fixed_charge_current: Setting CP '{self._internal_cp_key}' to 0 A")
                    self._internal_cp.data.set.current = 0
                    self._lm_status = yourcharge.LmStatus.Superseded
                else:
                    # fixed value >= 0.0 provided
                    log.info(f"Fixed current requested by yc_data.data.yc_control.fixed_charge_current: Setting CP '{self._internal_cp_key}' to {data.data.yc_data.data.yc_control.fixed_charge_current} A")
                    self._internal_cp.data.set.current = data.data.yc_data.data.yc_control.fixed_charge_current
                    self._lm_status = yourcharge.LmStatus.Superseded

        finally:
            self.send_status()


    def send_status(self):
        if self._previous_heartbeat_status != self._heartbeat_status:
            Pub().pub(f"{self.yc_status_topic}/heartbeat", self._heartbeat_status)
            self._previous_heartbeat_status = self._heartbeat_status
        if self._previous_lm_status != self._lm_status:
            Pub().pub(f"{self.yc_status_topic}/lm_status", self._lm_status)
            self._previous_lm_status = self._lm_status


    def do_load_control(self):
        log.info(f"Regular load control NOT YET IMPLEMENTED")
        pass


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
