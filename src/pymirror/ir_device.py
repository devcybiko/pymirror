#!/usr/bin/env python3
import subprocess
import os
import select
import time

# Command to run ir-keytable unbuffered
cmd = [
    "stdbuf", "-o0",
    "ir-keytable",
    "-v", "-t",
    "-p", "rc-5,rc-5-sz,jvc,sony,nec,sanyo,mce_kbd,rc-6,sharp,xmp"
]

proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
os.set_blocking(proc.stdout.fileno(), False)

print("Listening for IR events...")

# Track last press times
key_last_time = {}
KEY_UP_TIMEOUT = 0.2  # seconds

buffer = ""

try:
    while True:
        # Non-blocking read
        rlist, _, _ = select.select([proc.stdout], [], [], 0.01)
        if proc.stdout in rlist:
            chunk = proc.stdout.read(1024)
            if chunk:
                buffer += chunk
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line:
                        continue

                    now = time.time()

                    if "repeat" in line:
                        print(f"KEY REPEAT: {line}")
                        # Update last press time
                        scancode = line.split("scancode = ")[-1].split()[0]
                        key_last_time[scancode] = now

                    elif "scancode" in line:
                        print(f"KEY DOWN: {line}")
                        scancode = line.split("scancode = ")[-1].split()[0]
                        key_last_time[scancode] = now

        # Check for keys that timed out (assume released)
        expired = []
        for sc, t in key_last_time.items():
            if time.time() - t > KEY_UP_TIMEOUT:
                print(f"KEY UP: scancode = {sc}")
                expired.append(sc)
        for sc in expired:
            del key_last_time[sc]

except KeyboardInterrupt:
    print("Exiting...")
    proc.terminate()
    proc.wait()
