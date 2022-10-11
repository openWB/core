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
	# remove old backup files
	rm -v "$BACKUPDIR/"*
	BACKUPFILE="$BACKUPDIR/$FILENAME"

	# tell mosquitto to store all retained topics in db now
	echo "sending 'SIGUSR1' to mosquitto processes"
	sudo pkill -e -SIGUSR1 mosquitto
	# give mosquitto some time to finish
	sleep 0.2

	# create backup file
	echo "creating new backup file: $BACKUPFILE"
	echo "adding openWB files"
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
	echo "adding mosquitto files"
	sudo tar --verbose --append \
		--file="$BACKUPFILE" \
		--directory="/var/lib/" \
		"mosquitto/" "mosquitto_local/"
	echo "adding git information"
	git branch --no-color --show-current >"$OPENWBBASEDIR/ramdisk/GIT_BRANCH"
	git log --pretty='format:%H' -n1 >"$OPENWBBASEDIR/ramdisk/GIT_HASH"
	echo "branch: $(<"$OPENWBBASEDIR/ramdisk/GIT_BRANCH") commit-hash: $(<"$OPENWBBASEDIR/ramdisk/GIT_HASH")"
	tar --verbose --append \
		--file="$BACKUPFILE" \
		--directory="$OPENWBBASEDIR/ramdisk/" \
		"GIT_BRANCH" "GIT_HASH"
	echo "calculating checksums"
	# openwb directory
	find "$OPENWBBASEDIR" \( \
		-path "$OPENWBBASEDIR/.git" -o \
		-path "$OPENWBBASEDIR/data/backup" -o \
		-path "$OPENWBBASEDIR/.pytest" -o \
		-name "__pycache__" -o \
		-path "$OPENWBBASEDIR/.pytest_cache" -o \
		-path "$OPENWBBASEDIR/ramdisk" -o \
		-name "backup.log" \
		\) -prune -o \
		-type f -print0 | xargs -0 sha256sum | sed -n "s|$TARBASEDIR/||p" >"$OPENWBBASEDIR/ramdisk/SHA256SUM"
	# git info files
	find "$OPENWBBASEDIR/ramdisk/GIT_"* \
		-type f -print0 | xargs -0 sha256sum | sed -n "s|$OPENWBBASEDIR/ramdisk/||p" >>"$OPENWBBASEDIR/ramdisk/SHA256SUM"
	# mosquitto databases
	find "/var/lib/mosquitto"* \
		-type f -print0 | xargs -0 sudo sha256sum | sed -n "s|/var/lib/||p" >>"$OPENWBBASEDIR/ramdisk/SHA256SUM"
	tar --verbose --append \
		--file="$BACKUPFILE" \
		--directory="$OPENWBBASEDIR/ramdisk/" \
		"SHA256SUM"
	# cleanup
	echo "removing temporary files"
	rm -v "$OPENWBBASEDIR/ramdisk/GIT_BRANCH" "$OPENWBBASEDIR/ramdisk/GIT_HASH" "$OPENWBBASEDIR/ramdisk/SHA256SUM"
	tar --verbose --append \
		--file="$BACKUPFILE" \
		--directory="$OPENWBBASEDIR/data/log/" \
		"backup.log"
	echo "zipping archive"
	gzip --verbose "$BACKUPFILE"
	echo "setting permissions of new backup file"
	sudo chown openwb:www-data "$BACKUPFILE.gz"
	sudo chmod 664 "$BACKUPFILE.gz"

	echo "backup finished"
} >"$LOGFILE" 2>&1

# return our filename for further processing
echo "$FILENAME.gz"
