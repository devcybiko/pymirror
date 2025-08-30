import lirc

client = lirc.Client()

print(client.version())
