#!/bin/bash
# notify system about running reboot
mosquitto_pub -p 1886 -t "openWB/system/boot_done" -r -m 'false'
sleep 1

sudo reboot &
