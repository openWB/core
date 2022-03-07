#!/bin/bash

# fetch new release from GitHub
sudo git fetch origin

# stop openwb2 service
sudo service openwb2 stop

# only master branch yet
sudo git reset --hard "origin/master"

# now reboot system
sudo reboot now
