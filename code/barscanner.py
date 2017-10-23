import evdev
# import asyncio

# --------------- Barscanner class ---------------


class Barscanner:
    def __init__(self, device_name, code_ready_handle=None):
        self.device = evdev.InputDevice(device_name)
        self.read_code = ""
        self.code_ready_handle = code_ready_handle

    # Scancode: ASCIICode
    SCANCODES = {0: None, 1: u'ESC', 2: u'1', 3: u'2', 4: u'3', 5: u'4', 6: u'5', 7: u'6', 8: u'7', 9: u'8', 10: u'9',
                 11: u'0', 12: u'-', 13: u'=', 14: u'BKSP', 15: u'TAB', 16: u'Q', 17: u'W', 18: u'E', 19: u'R', 20: u'T',
                 21: u'Y', 22: u'U', 23: u'I', 24: u'O', 25: u'P', 26: u'[', 27: u']', 28: u'CRLF', 29: u'LCTRL', 30: u'A',
                 31: u'S', 32: u'D', 33: u'F', 34: u'G', 35: u'H', 36: u'J', 37: u'K', 38: u'L', 39: u';', 40: u'"',
                 41: u'`', 42: u'LSHFT', 43: u'\\', 44: u'Z', 45: u'X', 46: u'C', 47: u'V', 48: u'B', 49: u'N', 50: u'M',
                 51: u',', 52: u'.', 53: u'/', 54: u'RSHFT', 56: u'LALT', 100: u'RALT'}

    # Get corresponding ascii code for each event
    def map_code(self, data):
        return u'{}'.format(Barscanner.SCANCODES.get(data.scancode)) or u'UNKNOWN:[{}]'.format(data.scancode)

    # Get exclusive access to serial device
    def grab(self):
        self.device.grab()

    # Barscanner async read code coroutine
    async def read_code_coroutine(self):
        async for event in self.device.async_read_loop():
            if event.type == evdev.ecodes.EV_KEY:
                data = evdev.categorize(event)
                if data.keystate == 1:  # Down events only
                    key_lookup = self.map_code(data)

                    if data.scancode != 28:  # Building code
                        self.read_code += key_lookup
                    else:  # Code ready
                        self.code_ready_handle(self.read_code)
                        self.read_code = ''
