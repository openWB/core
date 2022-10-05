#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
OPENWBDIRNAME=${OPENWBBASEDIR##*/}
OPENWBDIRNAME=${OPENWBDIRNAME:-/}
TARBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
BACKUPDIR="$OPENWBBASEDIR/data/backup"
LOGFILE="$OPENWBBASEDIR/data/log/backup.log"

useExtendedFilename=$1
if ((useExtendedFilename == 1)); then
	FILENAME="openWB_backup_$(date +"%Y-%m-%d_%H:%M:%S").tar"
else
	FILENAME="backup.tar"
fi

{
	echo "deleting old backup files if present in '$BACKUPDIR'"
	rm -v "$BACKUPDIR/"*
	echo "creating new backup: $FILENAME"
	# remove old backup files
	BACKUPFILE="$BACKUPDIR/$FILENAME"

	# tell mosquitto to store all retained topics in db now
	echo "sending 'SIGUSR1' to mosquitto processes"
	sudo pkill -e -SIGUSR1 mosquitto
	# give mosquitto some time to finish
	sleep 0.2

	# create backup file
	echo "creating new backup file: $BACKUPFILE"
	tar --verbose --create \
		--file="$BACKUPFILE" \
		--directory="$TARBASEDIR/" \
		--exclude="$OPENWBDIRNAME/data/backup/*.tar" \
		--exclude="$OPENWBDIRNAME/data/log/backup.log" \
		--exclude="$OPENWBDIRNAME/.git" \
		--exclude "$OPENWBDIRNAME/ramdisk" \
		--exclude "__pycache__" \
		--exclude "$OPENWBDIRNAME/.pytest_cache" \
		"$OPENWBDIRNAME"
	sudo tar --verbose --append \
		--file="$BACKUPFILE" \
		--directory="/var/lib/" \
		"mosquitto/" "mosquitto_local/"
	tar --append \
		--file="$BACKUPFILE" \
		--directory="$OPENWBBASEDIR/data/log/" \
		"backup.log"
	echo "calculating checksums"
	find . \( \
		-path ./.git -o \
		-path ./data/backup -o \
		-path ./.pytest -o \
		-name __pycache__ -o \
		-path ./.pytest_cache -o \
		-path ./ramdisk -o \
		-name backup.log \
		\) -prune -o \
		-type f -print0 | xargs -0 sha256sum >"$OPENWBBASEDIR/ramdisk/SHA256SUM"
	tar --append \
		--file="$BACKUPFILE" \
		--directory="$OPENWBBASEDIR/ramdisk/" \
		"SHA256SUM"
	rm "$OPENWBBASEDIR/ramdisk/SHA256SUM"
	echo "zipping archive"
	gzip --verbose "$BACKUPFILE"
	echo "setting permissions of new backup file"
	sudo chown openwb:www-data "$BACKUPFILE.gz"
	sudo chmod 664 "$BACKUPFILE.gz"

	echo "backup finished"
} >"$LOGFILE" 2>&1

# return our filename for further processing
echo "$FILENAME.gz"
