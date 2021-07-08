#!/bin/bash
# Prüfen, ob .lock Datei existiert.Der Handler legt .lock-Dateien an. Nur wenn Handler und shell auf die Datei zugreifen, wird Locking benötigt.
# Wenn ja, locking durchführen.

OPENWBBASEDIR=$(cd `dirname $0`/../ && pwd)
. $OPENWBBASEDIR/helperFunctions.sh

lockfile=$1.lock
echo $lockfile
if [ -e $lockfile ]; then
	flock --timeout 1 $lockfile /var/www/html/openWB/runs/cleanupf.sh $1
	if [[ $? == 1 ]] ; then
		openwbDebugLog "MAIN" 0 "Lock fuer $lockfile fehl geschlagen."
	fi
else
    /var/www/html/openWB/runs/cleanupf.sh $1
fi
