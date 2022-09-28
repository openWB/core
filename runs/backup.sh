#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
BACKUPDIR="$OPENWBBASEDIR/data/backup"
LOGFILE="$OPENWBBASEDIR/ramdisk/backup.log"

useExtendedFilename=$1
if ((useExtendedFilename == 1)); then
	FILENAME="openWB_backup_$(date +"%Y-%m-%d_%H:%M:%S").tar.gz"
else
	FILENAME="backup.tar.gz"
fi

{
	echo "creating new backup: $FILENAME"
	# remove old backup files
	echo "deleting old backup files if present in '$BACKUPDIR'"
	rm -v "$BACKUPDIR/"*
	BACKUPFILE="$BACKUPDIR/$FILENAME"

	# tell mosquitto to store all retained topics in db now
	echo "sending 'SIGUSR1' to mosquitto processes"
	sudo pkill -e -SIGUSR1 mosquitto
	# give mosquitto some time to finish
	sleep 0.2

	# create backup file
	echo "creating new backup file: $BACKUPFILE"
	sudo tar --verbose --create --gzip \
		--exclude="$BACKUPDIR" \
		--exclude="$OPENWBBASEDIR/.git" \
		--exclude "$OPENWBBASEDIR/ramdisk" \
		--exclude "$OPENWBBASEDIR/__pycache__" \
		--exclude "$OPENWBBASEDIR/.pytest_cache" \
		--file="$BACKUPFILE" \
		"$OPENWBBASEDIR/" "/var/lib/mosquitto/" "/var/lib/mosquitto_local/"
	echo "setting permissions of new backup file"
	sudo chown openwb:www-data "$BACKUPFILE"
	sudo chmod 664 "$BACKUPFILE"

	echo "backup finished"
} >>"$LOGFILE" 2>&1

# return our filename for further processing
echo "$FILENAME"
