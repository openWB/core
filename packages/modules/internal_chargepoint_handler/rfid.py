import asyncio
import logging

from evdev import InputDevice, ecodes, list_devices, categorize
from helpermodules import pub
log = logging.getLogger(__name__)


class RfidReader:
    SCAN_CODE_MAP = {
        # function keys
        # 0: None,
        # ecodes.KEY_ESC: u'ESC',
        # ecodes.KEY_BACKSPACE: u'BKSP',
        # ecodes.KEY_TAB: u'TAB',
        # ecodes.KEY_LEFTBRACE: u'[',
        # ecodes.KEY_RIGHTBRACE: u']',
        # ecodes.KEY_ENTER: u'CRLF',
        # ecodes.KEY_LEFTCTRL: u'LCTRL',
        # ecodes.KEY_LEFTSHIFT: u'LSHFT',
        # ecodes.KEY_RIGHTSHIFT: u'RSHFT',
        # ecodes.KEY_LEFTALT: u'LALT',
        # ecodes.KEY_KPENTER: u'CRLF',
        # ecodes.KEY_RIGHTCTRL: u'RCTRL,
        # ecodes.KEY_RIGHTALT: u'RALT'

        # number keys
        ecodes.KEY_1: u'1',
        ecodes.KEY_2: u'2',
        ecodes.KEY_3: u'3',
        ecodes.KEY_4: u'4',
        ecodes.KEY_5: u'5',
        ecodes.KEY_6: u'6',
        ecodes.KEY_7: u'7',
        ecodes.KEY_8: u'8',
        ecodes.KEY_9: u'9',
        ecodes.KEY_0: u'0',
        ecodes.KEY_KP1: u'1',
        ecodes.KEY_KP2: u'2',
        ecodes.KEY_KP3: u'3',
        ecodes.KEY_KP4: u'4',
        ecodes.KEY_KP5: u'5',
        ecodes.KEY_KP6: u'6',
        ecodes.KEY_KP7: u'7',
        ecodes.KEY_KP8: u'8',
        ecodes.KEY_KP9: u'9',
        ecodes.KEY_KP0: u'0',

        # latin letters
        ecodes.KEY_A: u'A',
        ecodes.KEY_B: u'B',
        ecodes.KEY_C: u'C',
        ecodes.KEY_D: u'D',
        ecodes.KEY_E: u'E',
        ecodes.KEY_F: u'F',
        ecodes.KEY_G: u'G',
        ecodes.KEY_H: u'H',
        ecodes.KEY_I: u'I',
        ecodes.KEY_J: u'J',
        ecodes.KEY_K: u'K',
        ecodes.KEY_L: u'L',
        ecodes.KEY_M: u'M',
        ecodes.KEY_N: u'N',
        ecodes.KEY_O: u'O',
        ecodes.KEY_P: u'P',
        ecodes.KEY_Q: u'Q',
        ecodes.KEY_R: u'R',
        ecodes.KEY_S: u'S',
        ecodes.KEY_T: u'T',
        ecodes.KEY_U: u'U',
        ecodes.KEY_V: u'V',
        ecodes.KEY_W: u'W',
        ecodes.KEY_X: u'X',
        ecodes.KEY_Y: u'Y',
        ecodes.KEY_Z: u'Z',

        # punctuation marks and other characters
        ecodes.KEY_MINUS: u'-',
        ecodes.KEY_EQUAL: u'=',
        ecodes.KEY_SEMICOLON: u';',
        ecodes.KEY_COMMA: u',',
        ecodes.KEY_DOT: u'.',
        ecodes.KEY_SLASH: u'/',
        ecodes.KEY_KPASTERISK: u'*',
        ecodes.KEY_KPMINUS: u'-',
        ecodes.KEY_KPPLUS: u'+',
        ecodes.KEY_KPDOT: u'.',
        ecodes.KEY_KPSLASH: u'/',
        # ecodes.KEY_APOSTROPHE: u'"',
        # ecodes.KEY_GRAVE: u'`',
        # ecodes.KEY_BACKSLASH: u'\\',
    }
    _detected_keyboards: list[InputDevice] = []

    def __init__(self) -> None:
        try:
            devices = [InputDevice(path) for path in list_devices()]
            for device in devices:
                log.debug(f"**** {device.path} {device.name} {device.phys} ****")
                log.debug(device.capabilities(verbose=True))
                device_capabilities = device.capabilities()
                if ecodes.EV_KEY in device_capabilities:
                    log.debug("device emits keyboard events")
                    if ecodes.KEY_ENTER in device_capabilities[1]:
                        log.debug("detected 'enter' key, device seems to be a keyboard")
                        self._detected_keyboards.append(device)
                    else:
                        log.debug("no 'enter' key detected, skipping device")
                else:
                    log.debug("device does not emit keyboard events, skipping")
            log.info("detected keyboard devices:")
            for device in self._detected_keyboards:
                log.info(f"{device.path} {device.name}")
        except Exception:
            log.exception("Fehler im Rfid-Modul")

    def keyboards_detected(self) -> bool:
        return len(self._detected_keyboards) > 0

    async def _read_events(self, device: InputDevice):
        log.debug(f"reading events from: {device.path}")
        try:
            key_string = ""
            async for event in device.async_read_loop():
                if event.type == ecodes.EV_KEY:
                    data = categorize(event)
                    if data.keystate == 1:
                        if data.scancode in (ecodes.KEY_ENTER, ecodes.KEY_KPENTER):
                            if len(key_string) > 0:
                                log.debug(f"RFID-String: {key_string}")
                                pub.pub_single("openWB/set/internal_chargepoint/last_tag", key_string)
                                key_string = ""
                        else:
                            log.debug(f"new key: {data.scancode} - {ecodes.KEY[data.scancode]}")
                            key_lookup = self.SCAN_CODE_MAP.get(data.scancode) or u''
                            key_string += str(format(key_lookup))
        except Exception:
            log.exception("Fehler im Rfid-Modul")

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        for device in self._detected_keyboards:
            asyncio.ensure_future(self._read_events(device))
        loop.run_forever()
