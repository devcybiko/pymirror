#!/usr/bin/env python3
import select
import time
from evdev import InputDevice, ecodes


class IRDevice:
    def __init__(self, device_path="/dev/input/event0"):
        self.dev = InputDevice(device_path)
        # Timing thresholds (seconds)
        self.REPEAT_THRESHOLD = 0.25  # repeated keypress interval
        self.KEYUP_THRESHOLD = 0.30  # no signal -> key up
        # State
        self.last_scancode = None
        self.last_time = 0
        self.key_down = False
        self.key_name_lut = {}

    def set_key_name_lut(self, d: dict):
        self.key_name_lut = d
        pass

    def guess_protocol(self, sc):
        """Basic protocol guess based on scancode (customize per your remote)"""
        if sc & 0xFF00 == 0x0000:
            return "NEC"
        elif sc & 0xFF00 == 0x0100:
            return "RC5"
        elif sc & 0xFF00 == 0x0200:
            return "Sony"
        else:
            return "Unknown"

    def _new_event(self, protocol=None, scancode=None):
        return {
            "protocol": protocol,
            "scancode": scancode,
            "repeat": False,
            "pressed": False,
            "released": False,
            "key_name": 
        }

    def get_key_event(self):
        r, _, _ = select.select([self.dev], [], [], 0.05)  # 50ms timeout
        now = time.time()
        result = None

        if self.dev in r:
            for event in self.dev.read():
                if event.type == ecodes.EV_MSC:
                    scancode = event.value
                    protocol = self.guess_protocol(scancode)
                    result = self._new_event(protocol, scancode)

                    if scancode == self.last_scancode:
                        if (
                            self.key_down
                            and (now - self.last_time) < self.REPEAT_THRESHOLD
                        ):
                            result["repeat"] = True
                        else:
                            result["pressed"] = False
                            self.key_down = True
                    else:
                        result["repeat"] = True
                        self.key_down = True

                    self.last_scancode = scancode
                    self.last_time = now

                elif event.type == ecodes.EV_SYN:
                    pass  # end of event batch

        # Detect key up
        if (
            self.key_down
            and self.last_scancode is not None
            and (now - self.last_time) > self.KEYUP_THRESHOLD
        ):
            protocol = self.guess_protocol(self.last_scancode)
            result = self._new_event(protocol, self.last_scancode)
            result["released"] = True
            result["pressed"] = False
            self.key_down = False
            self.last_scancode = None

        if result and result["scancode"]:
            result["key_name"]
        return result


if __name__ == "__main__":
    ir = IRDevice()
    while True:
        event = ir.get_key_event()
        if event:
            print("event:", event)
