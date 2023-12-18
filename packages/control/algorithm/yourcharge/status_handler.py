import dataclasses
import datetime
import logging
import json

from dataclasses import dataclass

from typing import Dict, List
from control import data, yourcharge
from control.yourcharge import AccountingInfo, LmStatus
from helpermodules.pub import Pub


log = logging.getLogger(__name__)


@dataclass
class RfidInfo:
    rfid: str = None
    timestamp: str = None


class YcStatusHandler:
    def __init__(self) -> None:
        self._heartbeat_topic = f"{yourcharge.yc_status_topic}/heartbeat"
        self._lm_status_topic = f"{yourcharge.yc_status_topic}/lm_status"
        self._cp_enabled_status_topic = f"{yourcharge.yc_status_topic}/cp_enabled"
        self._cp_enabled_control_topic = f"{yourcharge.yc_control_topic}/cp_enabled"
        self._cp_meter_at_last_plugin_status_topic = f"{yourcharge.yc_status_topic}/cp_meter_at_last_plugin"
        self._cp_meter_at_last_plugin_control_topic = f"{yourcharge.yc_control_topic}/cp_meter_at_last_plugin"
        self._accounting_status_topic = f"{yourcharge.yc_status_topic}/accounting"
        self._energy_charged_since_plugin_control_topic = f"{yourcharge.yc_status_topic}/energy_charged_since_plugged"
        self._socket_approved_topic = f"{yourcharge.yc_status_topic}/socket_approved"
        self._scanned_rfid_topic = f"{yourcharge.yc_status_topic}/scanned_rfid"
        self._status_dict: Dict[str, object] = {}
        self._changed_keys: List[str] = []
        self._rfid_info_cache = None
        self._accounting_info_cache = None

    def publish_changes(self):
        try:
            for changed_key in self._changed_keys:
                new_value = self._status_dict[changed_key]
                log.info(f"Publishing status update: {changed_key} = '{new_value}'")
                Pub().pub(changed_key, new_value)
        finally:
            self._changed_keys.clear()

    # RFID scan
    def new_accounting(self, start_timestamp: datetime.datetime, meter_reading: float, charging: bool, plugged: bool) -> None:
        self._accounting_info_cache = AccountingInfo(timestamp=f"{start_timestamp.isoformat()}Z", meter_at_start=meter_reading, charging=charging, plugged_in=plugged)
        self._update(self._accounting_status_topic, dataclasses.asdict(self._accounting_info_cache))
        self._update(yourcharge.yc_accounting_control_topic, dataclasses.asdict(self._accounting_info_cache))

    def update_accounting(self, update_timestamp: datetime.datetime, current_meter: float, charging: bool, plugged: bool) -> None:
        self.get_accounting() # initializes the cache field
        self._accounting_info_cache.charging = charging
        self._accounting_info_cache.plugged_in = plugged
        self._accounting_info_cache.currrent_time = f"{update_timestamp.isoformat()}Z"
        self._accounting_info_cache.current_meter = current_meter
        self._update(self._accounting_status_topic, dataclasses.asdict(self._accounting_info_cache))
        self._update(yourcharge.yc_accounting_control_topic, dataclasses.asdict(self._accounting_info_cache))

    def get_accounting(self) -> AccountingInfo:
        if self._accounting_info_cache is None:
            if data.data.yc_data.data.yc_control.accounting is not None:
                self._accounting_info_cache = data.data.yc_data.data.yc_control.accounting
                self._update(self._accounting_status_topic, dataclasses.asdict(self._accounting_info_cache))
            else:
                self._accounting_info_cache = AccountingInfo()
                self._update(self._accounting_status_topic, dataclasses.asdict(self._accounting_info_cache))
                self._update(yourcharge.yc_accounting_control_topic, dataclasses.asdict(self._accounting_info_cache))
        return self._accounting_info_cache

    def has_changed_rfid_scan(self) -> bool:
        return self._scanned_rfid_topic in self._changed_keys

    # energy charged since last plugin
    def update_energy_charged_since_last_plugin(self, energy_value: float) -> None:
        self._update(self._energy_charged_since_plugin_control_topic, energy_value)

    def get_energy_charged_since_last_plugin(self) -> float:
        return self._get_status(self._energy_charged_since_plugin_control_topic)

    def has_changed_energy_charged_since_last_plugin(self) -> bool:
        return self._energy_charged_since_plugin_control_topic in self._changed_keys

    # CP meter at last plugin
    def update_cp_meter_at_last_plugin(self, meter_value: float) -> None:
        self._update(self._cp_meter_at_last_plugin_control_topic, meter_value)
        self._update(self._cp_meter_at_last_plugin_status_topic, meter_value)

    def get_cp_meter_at_last_plugin(self) -> float:
        return self._get_status(self._cp_meter_at_last_plugin_status_topic)

    def has_changed_cp_meter_at_last_plugin(self) -> bool:
        return self._cp_meter_at_last_plugin_status_topic in self._changed_keys

    # heartbeat
    def update_heartbeat_ok(self, hearbeat: bool) -> None:
        self._update(self._heartbeat_topic, hearbeat)

    def get_heartbeat_ok(self) -> bool:
        return self._get_status(self._heartbeat_topic)

    def has_changed_heartbeat(self) -> bool:
        return self._heartbeat_topic in self._changed_keys

    # lm status
    def update_lm_status(self, lm_status: LmStatus) -> None:
        self._update(self._lm_status_topic, lm_status)

    def get_lm_status(self) -> LmStatus:
        return self._get_status(self._lm_status_topic)

    def has_changed_lm_status(self) -> bool:
        return self._lm_status_topic in self._changed_keys

    # CP enabled
    def update_cp_enabled(self, lm_status: LmStatus) -> None:
        self._update(self._cp_enabled_control_topic, lm_status)
        self._update(self._cp_enabled_status_topic, lm_status)

    def get_cp_enabled(self) -> LmStatus:
        return self._get_status(self._cp_enabled_status_topic)

    def has_changed_cp_enabled(self) -> bool:
        return self._cp_enabled_status_topic in self._changed_keys

    # Socket approved
    def update_socket_approved(self, socket_approved: bool) -> None:
        self._update(self._socket_approved_topic, socket_approved)

    def get_socket_approved(self) -> bool:
        return self._get_status(self._socket_approved_topic)

    def has_changed_socket_approved(self) -> bool:
        return self._socket_approved_topic in self._changed_keys

    # RFID scan
    def update_rfid_scan(self, rfid: str, timestamp: datetime.datetime = datetime.datetime.utcnow()) -> None:
        self._rfid_info_cache = RfidInfo(rfid=rfid, timestamp=f"{timestamp.isoformat()}Z")
        self._update(self._scanned_rfid_topic, dataclasses.asdict(self._rfid_info_cache))

    def get_rfid_scan(self) -> RfidInfo:
        if self._rfid_info_cache is None:
            rfidinfo_string = self._get_status(self._scanned_rfid_topic)
            if rfidinfo_string is None or rfidinfo_string == "":
                self._rfid_info_cache = RfidInfo(rfid=None, timestamp=None)
            else:
                self._rfid_info_cache = json.loads(rfidinfo_string)
        return self._rfid_info_cache

    def has_changed_rfid_scan(self) -> bool:
        return self._scanned_rfid_topic in self._changed_keys

    # internal methods
    def _get_status(self, key: str):
        return self._status_dict.get(key)

    def _update(self, key: str, value: object):
        if not key in self._status_dict or value != self._status_dict[key]:
            self._changed_keys.append(key)
            log.info(f"Status change: {key} changed form '{self._status_dict.get(key)}' to '{value}'")
            self._status_dict[key] = value
