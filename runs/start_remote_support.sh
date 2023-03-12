#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "$0")/../" && pwd)

sshpass -p "$1" ssh -tt -o StrictHostKeyChecking=no -o "ServerAliveInterval 60" -R "$2":localhost:22 "$3@remotesupport.openwb.de" &

echo $! >"${OPENWBBASEDIR}/ramdisk/remotesupportpid"
