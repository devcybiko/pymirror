#!/usr/bin/env python3
import subprocess
import os
import select

# Command to run ir-keytable unbuffered
cmd = [
    "stdbuf", "-o0",
    "ir-keytable",
    "-v", "-t",
    "-p", "rc-5,rc-5-sz,jvc,sony,nec,sanyo,mce_kbd,rc-6,sharp,xmp"
]

# Start subprocess
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
os.set_blocking(proc.stdout.fileno(), False)

print("Listening for IR events...")

try:
    buffer = ""
    while True:
        # Use select to check if data is available
        rlist, _, _ = select.select([proc.stdout], [], [], 0.01)
        if proc.stdout in rlist:
            chunk = proc.stdout.read(1024)
            if chunk:
                buffer += chunk
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if line:
                        # Detect key down / repeat / key up
                        if "repeat" in line:
                            print(f"KEY REPEAT: {line}")
                        elif "scancode" in line:
                            print(f"KEY DOWN: {line}")
                        else:
                            print(f"OTHER: {line}")

except KeyboardInterrupt:
    print("Exiting...")
    proc.terminate()
    proc.wait()
