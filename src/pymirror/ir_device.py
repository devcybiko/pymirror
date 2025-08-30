#!/usr/bin/env python3
import select
import time
from evdev import InputDevice, ecodes


class IRDevice:
    def __init__(self, device_path="/dev/input/event0")
        self.dev = InputDevice(DEVICE_PATH)


# State
last_scancode = None
last_time = 0
key_down = False

def guess_protocol(sc):
    """Basic protocol guess based on scancode (customize per your remote)"""
    if sc & 0xFF00 == 0x0000:
        return "NEC"
    elif sc & 0xFF00 == 0x0100:
        return "RC5"
    elif sc & 0xFF00 == 0x0200:
        return "Sony"
    else:
        return "Unknown"

print(f"Listening for IR scancodes on {DEVICE_PATH} with key-up detection...")

try:
    while True:
        r, _, _ = select.select([dev], [], [], 0.05)  # 50ms timeout
        now = time.time()

        if dev in r:
            for event in dev.read():
                if event.type == ecodes.EV_MSC:
                    scancode = event.value
                    protocol = guess_protocol(scancode)

                    if scancode == last_scancode:
                        if key_down and (now - last_time) < self.REPEAT_THRESHOLD:
                            print(f"{protocol}: scancode=0x{scancode:X} repeat")
                        else:
                            print(f"{protocol}: scancode=0x{scancode:X} pressed")
                            key_down = True
                    else:
                        print(f"{protocol}: scancode=0x{scancode:X} pressed")
                        key_down = True

                    last_scancode = scancode
                    last_time = now

                elif event.type == ecodes.EV_SYN:
                    pass  # end of event batch
        # print("...")

        # Detect key up
        if key_down and last_scancode is not None and (now - last_time) > self.KEYUP_THRESHOLD:
            protocol = guess_protocol(last_scancode)
            print(f"{protocol}: scancode=0x{last_scancode:X} released")
            key_down = False
            last_scancode = None

except KeyboardInterrupt:
    print("\nExiting...")
