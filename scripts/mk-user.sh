#!/bin/bash

NEW_USER="pymirror"
sudo adduser "$NEW_USER"
sudo usermod -aG sudo "$NEW_USER"
sudo groupadd wheel
sudo usermod -aG wheel "$NEW_USER"
sudo usermod -aG gpio,i2c,spi,video,audio,wheel "$NEW_USER"

# sudo vi /etc/pam.d/su
# auth       sufficient pam_wheel.so trust