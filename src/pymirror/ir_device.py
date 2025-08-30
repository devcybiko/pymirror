#!/usr/bin/env python3
import subprocess
import threading
import queue
import sys

def enqueue_output(out, q):
    for line in iter(out.readline, b''):
        q.put(line.decode().strip())
    out.close()

# Command to run
cmd = [
    "ir-keytable",
    "-v",
    "-t",
    "-p", "rc-5,rc-5-sz,jvc,sony,nec,sanyo,mce_kbd,rc-6,sharp,xmp"
]

# Start the subprocess
proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=1)

# Queue to store stdout lines
q = queue.Queue()

# Start thread to read stdout
t = threading.Thread(target=enqueue_output, args=(proc.stdout, q))
t.daemon = True  # Thread dies with the program
t.start()

print("Listening for IR key events...")

try:
    while True:
        try:
            line = q.get_nowait()  # Non-blocking
        except queue.Empty:
            print("...")
            # No line available, do other work here
            continue
        if line:
            # Example parsing
            if "scancode" in line:
                print("IR:", line)
except KeyboardInterrupt:
    print("Exiting...")
    proc.terminate()
    t.join()
    sys.exit(0)
