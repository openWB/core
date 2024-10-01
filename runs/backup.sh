#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
OPENWBDIRNAME=${OPENWBBASEDIR##*/}
OPENWBDIRNAME=${OPENWBDIRNAME:-/}
TARBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
BACKUPDIR="$OPENWBBASEDIR/data/backup"
RAMDISKDIR="$OPENWBBASEDIR/ramdisk"
TEMPDIR="$RAMDISKDIR/temp"
LOGDIR="$OPENWBBASEDIR/data/log"
LOGFILE="$LOGDIR/backup.log"

useExtendedFilename=$1
if ((useExtendedFilename == 1)); then
	# only use characters supported in most OS!
	# for Win see https://learn.microsoft.com/en-us/rest/api/storageservices/naming-and-referencing-shares--directories--files--and-metadata
	FILENAME="openWB_backup_$(date +"%Y-%m-%d_%H-%M-%S").tar"
else
	FILENAME="backup.tar"
fi

{
	echo "starting backup script"
	echo "environment:"
	echo "  OPENWBBASEDIR: $OPENWBBASEDIR"
	echo "  OPENWBDIRNAME: $OPENWBDIRNAME"
	echo "  TARBASEDIR: $TARBASEDIR"
	echo "  BACKUPDIR: $BACKUPDIR"
	echo "  RAMDISKDIR: $RAMDISKDIR"
	echo "  TEMPDIR: $TEMPDIR"
	echo "  LOGDIR: $LOGDIR"
	echo "  LOGFILE: $LOGFILE"
	echo "  FILENAME: $FILENAME"

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
		"$OPENWBDIRNAME/data/charge_log" \
		"$OPENWBDIRNAME/data/daily_log" \
		"$OPENWBDIRNAME/data/monthly_log" \
		"$OPENWBDIRNAME/data/log/uuid"
	echo "adding configuration file"
	sudo tar --verbose --append \
		--file="$BACKUPFILE" \
		--directory="/home/openwb/" \
		"configuration.json"
	echo "adding mosquitto files"
	sudo tar --verbose --append \
		--file="$BACKUPFILE" \
		--directory="/var/lib/" \
		"mosquitto/" "mosquitto_local/"
	# ToDo: add mosquitto configuration files
	echo "adding git information"
	git branch --no-color --show-current >"$RAMDISKDIR/GIT_BRANCH"
	git log --pretty='format:%H' -n1 >"$RAMDISKDIR/GIT_HASH"
	echo "branch: $(<"$RAMDISKDIR/GIT_BRANCH") commit-hash: $(<"$RAMDISKDIR/GIT_HASH")"
	tar --verbose --append \
		--file="$BACKUPFILE" \
		--directory="$RAMDISKDIR/" \
		"GIT_BRANCH" "GIT_HASH"

	echo "calculating checksums"
	IFS=$'\n'
	mapfile -t file_list < <(tar -tf "$BACKUPFILE")
	mkdir -p "$TEMPDIR"
	# process each file
	for file in "${file_list[@]}"; do
		# skip directories
		if [[ $file =~ /$ ]]; then
			echo "skipping directory $file"
			continue
		fi
		# extract the file
		tar -xf "$BACKUPFILE" -C "$TEMPDIR" "$file"
		# calculate the checksum
		sha256sum "$TEMPDIR/$file" | sed -n "s|$TEMPDIR/||p" >> "$RAMDISKDIR/SHA256SUM"
		# remove the file
		rm -f "$TEMPDIR/$file"
	done
	tar --verbose --append \
		--file="$BACKUPFILE" \
		--directory="$RAMDISKDIR/" \
		"SHA256SUM"

	# cleanup
	echo "removing temporary files"
	rm -v "$RAMDISKDIR/GIT_BRANCH" "$RAMDISKDIR/GIT_HASH" "$RAMDISKDIR/SHA256SUM"
	rm -rf "${TEMPDIR:?}/"
	tar --append \
		--file="$BACKUPFILE" \
		--directory="$LOGDIR/" \
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
