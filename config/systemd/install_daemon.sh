#!/bin/bash

sudo cp fecoteme_access_control.service /lib/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable fecoteme_access_control
sudo systemctl start fecoteme_access_control
