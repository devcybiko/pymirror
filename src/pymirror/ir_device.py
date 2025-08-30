import subprocess
import os
import time

# Command: ir-keytable in test mode with all protocols
cmd = [
    "ir-keytable",
    "-v", "-t",
    "-p", "rc-5,rc-5-sz,jvc,sony,nec,sanyo,mce_kbd,rc-6,sharp,xmp"
]

# Start subprocess
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

# Make stdout non-blocking
os.set_blocking(proc.stdout.fileno(), False)

try:
    while True:
        try:
            line = proc.stdout.readline()
            if line:
                print(line.strip())
        except BlockingIOError:
            # No data available yet
            pass
        
        # Optional: do other stuff here
        time.sleep(0.01)

except KeyboardInterrupt:
    print("Exiting...")
    proc.terminate()
    proc.wait()
