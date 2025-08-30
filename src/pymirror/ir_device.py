#!/usr/bin/env python3
import select
import time
from evdev import InputDevice, ecodes

LUT = {
        69: "KEY_ONE",
        70: "KEY_TWO",
        71: "KEY_THREE",
        68: "KEY_FOUR",
        64: "KEY_FIVE",
        67: "KEY_SIX",
        7: "KEY_SEVEN",
        21: "KEY_EIGHT",
        9: "KEY_NINE",
        25: "KEY_ZERO",
        22: "KEY_NUMBERSIGN",
        13: "KEY_ASTERISK",
        24: "KEY_UP",
        8: "KEY_LEFT",
        90: "KEY_RIGHT",
        82: "KEY_DOWN",
        28: "KEY_ENTER"
    }

class IRDevice:
    def __init__(self, device_path="/dev/input/event0", lut=LUT):
        self.dev = InputDevice(device_path)
        # Timing thresholds (seconds)
        self.REPEAT_THRESHOLD = 0.10  # repeated keypress interval
        self.KEYUP_THRESHOLD = 0.10  # no signal -> key up
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
            "key_name": None
        }

    def get_key_event(self):
        r, _, _ = select.select([self.dev], [], [], 0)  # Non-blocking (0 timeout)
        now = time.time()
        result = None
        
        if self.dev in r:
            # Read all available events - this should drain the queue
            try:
                events = self.dev.read()  # This returns a list of all available events
                for event in events:
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
                                result["pressed"] = True
                            else:
                                # Same key pressed after key-up threshold - treat as new press
                                result["pressed"] = True
                                self.key_down = True
                        else:
                            # Different key - implicitly release previous key and press new one
                            if self.last_scancode is not None and self.key_down:
                                # Previous key was stuck down, implicitly release it
                                self.key_down = False
                            result["pressed"] = True
                            self.key_down = True

                        self.last_scancode = scancode
                        self.last_time = now
                        
                        # Return immediately on first MSC event - process one at a time
                        if result and result["scancode"]:
                            result["key_name"] = self.key_name_lut.get(result["scancode"])
                        return result

                    elif event.type == ecodes.EV_SYN:
                        pass  # end of event batch
            except BlockingIOError:
                # No more events available
                pass

        # Detect key up (only if no new event was processed)
        if (
            result is None  # No new event
            and self.key_down
            and self.last_scancode is not None
            and (now - self.last_time) > self.KEYUP_THRESHOLD
        ):
            protocol = self.guess_protocol(self.last_scancode)
            result = self._new_event(protocol, self.last_scancode)
            result["released"] = True
            result["pressed"] = False
            self.key_down = False
            # Don't reset last_scancode here - keep it for reference

        if result and result["scancode"]:
            result["key_name"] = self.key_name_lut.get(result["scancode"])

        return result


if __name__ == "__main__":
    ir = IRDevice()

    while True:
        event = ir.get_key_event()
        if event:
            print("event:", event)
