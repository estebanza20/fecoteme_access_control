#!/usr/bin/bash

#Access control prerrequisites for Raspbian 9.1 (stretch)

# Python related
sudo apt-get install python3-dev
sudo apt-get install python3-pip

# Install RPi.GPIO
sudo apt-get install python3-rpi.gpio

# Install evdev
sudo pip3 install evdev

# Install mysqlclient
sudo apt-get install mysql-server mysql-client
sudo apt-get install python3-mysqldb

# Install dateutil
sudo apt-get intall python3-dateutil

