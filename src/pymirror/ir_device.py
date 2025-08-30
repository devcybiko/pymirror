#!/usr/bin/env python3
import select
import time
from evdev import InputDevice, ecodes


class IRDevice:
    def __init__(self, device_path="/dev/input/event0")
        self.dev = InputDevice(device_path)
        # Timing thresholds (seconds)
        self.REPEAT_THRESHOLD = 0.25  # repeated keypress interval
        self.KEYUP_THRESHOLD = 0.30   # no signal -> key up
        # State
        self.last_scancode = None
        self.last_time = 0
        self.key_down = False



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

    def get_key_event(self):
    try:
        while True:
            r, _, _ = select.select([dev], [], [], 0.05)  # 50ms timeout
            now = time.time()

            if dev in r:
                for event in dev.read():
                    if event.type == ecodes.EV_MSC:
                        scancode = event.value
                        protocol = guess_protocol(scancode)

                        if scancode == self.last_scancode:
                            if self.key_down and (now - self.last_time) < self.REPEAT_THRESHOLD:
                                print(f"{protocol}: scancode=0x{scancode:X} repeat")
                            else:
                                print(f"{protocol}: scancode=0x{scancode:X} pressed")
                                self.key_down = True
                        else:
                            print(f"{protocol}: scancode=0x{scancode:X} pressed")
                            self.key_down = True

                        self.last_scancode = scancode
                        self.last_time = now

                    elif event.type == ecodes.EV_SYN:
                        pass  # end of event batch
            # print("...")

            # Detect key up
            if self.key_down and self.last_scancode is not None and (now - self.last_time) > self.KEYUP_THRESHOLD:
                protocol = guess_protocol(self.last_scancode)
                print(f"{protocol}: scancode=0x{self.last_scancode:X} released")
                self.key_down = False
                self.last_scancode = None

    except KeyboardInterrupt:
        print("\nExiting...")
