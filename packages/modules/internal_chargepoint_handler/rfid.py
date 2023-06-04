import evdev
import logging
from evdev import InputDevice

from helpermodules import pub
log = logging.getLogger(__name__)


class RfidReader:
    SCAN_CODES = {
        0: None, 1: u'ESC', 2: u'1', 3: u'2', 4: u'3', 5: u'4', 6: u'5', 7: u'6', 8: u'7', 9: u'8',
        10: u'9', 11: u'0', 12: u'-', 13: u'=', 14: u'BKSP', 15: u'TAB', 16: u'Q', 17: u'W', 18: u'E', 19: u'R',
        20: u'T', 21: u'Y', 22: u'U', 23: u'I', 24: u'O', 25: u'P', 26: u'[', 27: u']', 28: u'CRLF', 29: u'LCTRL',
        30: u'A', 31: u'S', 32: u'D', 33: u'F', 34: u'G', 35: u'H', 36: u'J', 37: u'K', 38: u'L', 39: u';',
        40: u'"', 41: u'`', 42: u'LSHFT', 43: u'\\', 44: u'Z', 45: u'X', 46: u'C', 47: u'V', 48: u'B', 49: u'N',
        50: u'M', 51: u',', 52: u'.', 53: u'/', 54: u'RSHFT', 56: u'LALT', 100: u'RALT'
    }

    def __init__(self, device: str) -> None:
        try:
            try:
                self.input_device = InputDevice(f"/dev/input/{device}")
            except FileNotFoundError:
                log.debug(f"Input-Event {device} nicht gefunden.")
        except Exception:
            log.exception("Fehler im Rfid-Modul")

    def loop(self):
        try:
            key_string = ""
            for event in self.input_device.read_loop():
                if event.type == evdev.ecodes.EV_KEY:
                    data = evdev.categorize(event)
                    if data.keystate == 1:
                        key_lookup = self.SCAN_CODES.get(data.scancode) or u'UNKNOWN:{}'.format(data.scancode)
                        key_string += str(format(key_lookup))
                        if "CRLF" in key_string:
                            key_string = key_string[:-4]
                            log.debug(f"RFID-String: {key_string}")
                            pub.pub_single("openWB/set/internal_chargepoint/last_tag", key_string)
                            key_string = ""
        except Exception:
            log.exception("Fehler im Rfid-Modul")
