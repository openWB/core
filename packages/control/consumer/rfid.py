from fnmatch import fnmatch

from control import data
from control.consumer.consumer_data import ConsumerRfidProtocol, RfidReset
from control.consumer.usage import NOT_CONTROLLED
from helpermodules import timecheck


RFID_SUPPORTED_MODULE_TYPES = ("mqtt", "wallbox_socket")


def rfid_supported(module) -> bool:
    return getattr(module, "type", None) in RFID_SUPPORTED_MODULE_TYPES


class ConsumerRfidMixin:
    def rfid_required(self: ConsumerRfidProtocol) -> bool:
        return (self.data.usage.type not in NOT_CONTROLLED and self.data.extra_meter is None and
                rfid_supported(self.data.module) and self.data.config.rfid_enabled and
                data.data.optional_data.data.rfid.active)

    def update_rfid(self: ConsumerRfidProtocol) -> None:
        state = self.data.set
        tag = self.data.get.rfid
        if tag is not None:
            if self.rfid_required():
                if any(fnmatch(tag.lower(), pattern.lower()) for pattern in self.data.config.valid_tags):
                    state.rfid = tag
                    state.rfid_timestamp = (self.data.get.rfid_timestamp if self.data.get.rfid_timestamp is not None
                                            else timecheck.create_timestamp())
                    state.rfid_power_seen = False
                    state.rfid_power_end = None
                else:
                    self.set_state_and_log(f"Der ID-Tag {tag} ist diesem Verbraucher nicht zugeordnet.")
            self.clear_rfid()
        if not self.rfid_required():
            self.reset_rfid()
            return
        if state.rfid is None:
            return
        now = timecheck.create_timestamp()
        if self.data.config.rfid_reset == RfidReset.AFTER_POWER_END:
            if self.data.get.charge_state:
                state.rfid_power_seen = True
                state.rfid_power_end = None
            elif state.rfid_power_seen and state.rfid_power_end is None:
                state.rfid_power_end = now
            timestamp = state.rfid_power_end
        else:
            timestamp = state.rfid_timestamp
        if timestamp is not None and now - timestamp >= self.data.config.rfid_timeout:
            self.reset_rfid()

    def clear_rfid(self: ConsumerRfidProtocol) -> None:
        """Verarbeiteten Eingangstag löschen."""
        self.data.get.rfid = None
        self.data.get.rfid_timestamp = None
        self.module.clear_rfid()

    def reset_rfid(self: ConsumerRfidProtocol) -> None:
        self.data.set.rfid = None
        self.data.set.rfid_timestamp = None
        self.data.set.rfid_power_seen = False
        self.data.set.rfid_power_end = None
