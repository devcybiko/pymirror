import lirc

# Connect to the running lircd daemon
sock = lirc.init("myprogram", blocking=False)

try:
    while True:
        codes = lirc.nextcode()
        if codes:
            print("IR codes:", codes)
except KeyboardInterrupt:
    pass
finally:
    lirc.deinit()
