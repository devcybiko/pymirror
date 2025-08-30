import socket

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect("/var/run/lirc/lircd")

while True:
    data = sock.recv(128)
    
    if data:
        print(data.decode().strip())
