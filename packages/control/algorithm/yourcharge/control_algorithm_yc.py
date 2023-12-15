import datetime
import logging

from control import data, yourcharge
from control.chargepoint.chargepoint import Chargepoint

log = logging.getLogger(__name__)


class ControlAlgorithmYc:
    def __init__(self, cp_key: str, cp_handle: Chargepoint) -> None:
        self._last_control_run = datetime.datetime(1, 1, 1, 0, 0, 0)
        self._internal_cp_key = cp_key
        self._internal_cp = cp_handle

    def do_load_control(self):
        if not data.data.yc_data.data.yc_control.fixed_charge_current is None:
            # handling of superseded, fixed charge current
            if data.data.yc_data.data.yc_control.fixed_charge_current < 0.0:
                # invalid or default value < 0.0
                self._set_current("Charging disapproved by yc_data.data.yc_control.fixed_charge_current", 0.0, yourcharge.LmStatus.DownByError)
            else:
                # fixed value >= 0.0 provided
                log.info(f": Setting CP '{self._internal_cp_key}' charge current to {data.data.yc_data.data.yc_control.fixed_charge_current} A")
                self._set_current("Fixed current requested by yc_data.data.yc_control.fixed_charge_current", data.data.yc_data.data.yc_control.fixed_charge_current, yourcharge.LmStatus.Superseded)
            return

        # check if control interval is actuall due
        now_it_is = datetime.datetime.utcnow()
        if (now_it_is - self._last_control_run).total_seconds() < data.data.yc_data.data.yc_config.minimum_adjustment_interval:
            log.info(f"Control loop not yet due")
            return
        self._last_control_run = now_it_is

        # now we can start with actual load control calculation
        log.info("Regular load control NOT YET IMPLEMENTED")
        pass

    def _set_current(self, justification: str, current: float, status: yourcharge.LmStatus):
        self._status_handler.update_lm_status(status)
        if abs(self._internal_cp.data.set.current - current) > 0.001:
            log.info(f"{justification}: Setting CP '{self._internal_cp_key}' charge current to {current} A (status {status})")
            self._internal_cp.data.set.current = current
