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
HOMEDIR="/home/openwb"
KEYFILE="backup.key"
VAR_LIB="/var/lib"

# Mosquitto DB files to monitor
DB_FILES=(
	"$VAR_LIB/mosquitto/mosquitto.db"
	"$VAR_LIB/mosquitto_local/mosquitto.db"
)

useExtendedFilename=$1
FILENAMESUFFIX=".openwb-backup"

generate_filename() {
	# generate filename
	# if useExtendedFilename is 1, use date and version info
	# else just use "backup"
	if ((useExtendedFilename == 1)); then
		# only use characters supported in most OS!
		# for Win see https://learn.microsoft.com/en-us/rest/api/storageservices/naming-and-referencing-shares--directories--files--and-metadata
		FILENAME="$(date +"%Y-%m-%d_%H-%M-%S")_$(<"$OPENWBBASEDIR"/web/version)"
	else
		FILENAME="backup"
	fi
	BACKUPFILE="$BACKUPDIR/$FILENAME"
}

log_environment() {
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
}

remove_old_backups() {
	echo "removing old files in '$BACKUPDIR' if present"
	# Delete old backups (robust, no glob issues)
	find "$BACKUPDIR" -mindepth 1 -maxdepth 1 -not -name '.donotdelete' -exec rm -vrf {} +
}

force_mosquitto_write() {
	collect_baseline() {
		echo "collecting Baseline-mtime before SIGUSR1:"
		# Baseline mtimes to avoid race condition (captured before SIGUSR1)
		declare -Ag BASELINE_DB_MTIME=()

		for f in "${DB_FILES[@]}"; do
			if [ -e "$f" ]; then
				BASELINE_DB_MTIME["$f"]=$(stat -c %Y "$f")
				echo "  $f -> ${BASELINE_DB_MTIME["$f"]}"
			else
				BASELINE_DB_MTIME["$f"]=0
				echo "  $f -> (does not yet exist, setting to 0)"
			fi
		done
	}

	flush_mosquitto() {
		# inform mosquitto to flush data to disk
		echo "sending 'SIGUSR1' to mosquitto processes to flush data to disk"
		sudo pkill -e -SIGUSR1 mosquitto || echo "WARNING: no processes found?"
	}

	wait_for_mosquitto_flush() {
		# wait for mosquitto to flush db files to disk
		# timeout after 5 seconds
		# uses inotifywait if available, else falls back to polling
		# requires inotify-tools package for inotifywait
		local timeout=5
		local start_ts
		start_ts=$(date +%s)
		declare -A initial_mtime

		# Use previously captured baseline (recorded before signal)
		if ((${#BASELINE_DB_MTIME[@]})); then
			echo "using previously collected Baseline-mtime values:"
			for f in "${DB_FILES[@]}"; do
				initial_mtime["$f"]=${BASELINE_DB_MTIME["$f"]:-0}
				echo "  $f -> ${initial_mtime["$f"]}"
			done
		else
			# Fallback (should not occur)
			for f in "${DB_FILES[@]}"; do
				[ -e "$f" ] && initial_mtime["$f"]=$(stat -c %Y "$f") || initial_mtime["$f"]=0
			done
		fi

		echo "waiting for mosquitto to flush db files (timeout ${timeout}s)..."

		if command -v inotifywait >/dev/null 2>&1; then
			echo "using 'inotifywait'"
			local pending=()
			for f in "${DB_FILES[@]}"; do
				pending+=("$f")
			done
			while ((${#pending[@]})); do
				local elapsed=$(( $(date +%s) - start_ts ))
				local remain=$(( timeout - elapsed ))
				(( remain <= 0 )) && echo "timeout reached (inotify), continuing." && break
				inotifywait -q -t "$remain" -e modify -e close_write -e attrib -e move -e create "${pending[@]}" 2>/dev/null || true
				local new_pending=()
				for f in "${pending[@]}"; do
					if [ -e "$f" ]; then
						local mt
						mt=$(stat -c %Y "$f")
						if (( mt != initial_mtime["$f"] )); then
							echo "modified: $f (old: ${initial_mtime["$f"]} -> new: $mt)"
						else
							new_pending+=("$f")
						fi
					else
						new_pending+=("$f")
					fi
				done
				pending=("${new_pending[@]}")
			done
		else
			echo "'inotifywait' not found, falling back to polling"
			while true; do
				local all_ok=1
				for f in "${DB_FILES[@]}"; do
					if [ -e "$f" ]; then
						local mt
						mt=$(stat -c %Y "$f")
						if (( mt != initial_mtime["$f"] )); then
							echo "modified (polling): $f (old: ${initial_mtime["$f"]} -> new: $mt)"
							initial_mtime["$f"]=$mt
						else
							all_ok=0
						fi
					else
						all_ok=0
					fi
				done
				(( all_ok == 1 )) && echo "all relevant files are modified" && break
				local elapsed=$(( $(date +%s) - start_ts ))
				(( elapsed >= timeout )) && echo "timeout reached (polling), continuing." && break
				sleep 0.1
			done
		fi
	}

	collect_baseline
	flush_mosquitto
	wait_for_mosquitto_flush
}

collect_git_info() {
	echo "collecting git information"
	git branch --no-color --show-current >"$RAMDISKDIR/GIT_BRANCH"
	git log --pretty='format:%H' -n1 >"$RAMDISKDIR/GIT_HASH"
	echo "branch: $(<"$RAMDISKDIR/GIT_BRANCH") commit-hash: $(<"$RAMDISKDIR/GIT_HASH")"
}

create_archive() {
	prepare_rel_db_files() {
		# prepare relative db paths for tar's --directory=$VAR_LIB/
		rel_db_files=()
		for f in "${DB_FILES[@]}"; do
			if [[ $f == $VAR_LIB/* ]]; then
				rel_db_files+=("${f#"$VAR_LIB"/}")
			else
				# falls Eintrag nicht unter $VAR_LIB liegt, belasse ihn unverändert
				rel_db_files+=("$f")
			fi
		done
	}

	create_backup() {
		echo "creating new backup file: $BACKUPFILE"
		echo "adding files"

		sudo tar --verbose --create \
			--file="$BACKUPFILE" \
			--directory="$VAR_LIB/" \
				"${rel_db_files[@]}" \
			--directory="/etc/mosquitto/" \
				"conf_local.d/" \
			--directory="$TARBASEDIR/" \
				"$OPENWBDIRNAME/data/charge_log" \
				"$OPENWBDIRNAME/data/daily_log" \
				"$OPENWBDIRNAME/data/monthly_log" \
				"$OPENWBDIRNAME/data/log/uuid" \
			--directory="$HOMEDIR/" \
				"configuration.json" \
			--directory="/" \
				"boot/config.txt" \
			--directory="$RAMDISKDIR/" \
				"GIT_BRANCH" \
				"GIT_HASH"
	}

	calculate_checksums() {
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

		echo "adding checksum file to archive"
		sudo tar --verbose --append \
			--file="$BACKUPFILE" \
			--directory="$RAMDISKDIR/" \
				"SHA256SUM"
	}

	cleanup_and_compress() {
		echo "removing temporary files"
		rm -v "$RAMDISKDIR/GIT_BRANCH" "$RAMDISKDIR/GIT_HASH" "$RAMDISKDIR/SHA256SUM"
		rm -rf "${TEMPDIR:?}/"
		echo "adding log file to archive"
		sudo tar --append \
			--file="$BACKUPFILE" \
			--directory="$LOGDIR/" \
				"backup.log"
		echo "zipping archive"
		gzip --verbose --suffix "$FILENAMESUFFIX" "$BACKUPFILE"
	}

	encrypt_backup() {
		# encrypt backup file with gpg
		if [[ -f "$HOMEDIR/$KEYFILE" ]]; then
			echo "encrypting backup file"
			gpg --batch --yes --passphrase-file "$HOMEDIR/$KEYFILE" \
				--symmetric --cipher-algo AES256 "$BACKUPFILE$FILENAMESUFFIX"
			echo "removing unencrypted backup file"
			rm -v "$BACKUPFILE$FILENAMESUFFIX"
			FILENAMESUFFIX="$FILENAMESUFFIX.gpg"
		else
			echo "No key found at '$HOMEDIR/$KEYFILE', skipping encryption!"
		fi
	}

	fix_permissions() {
		echo "setting permissions of new backup file"
		sudo chown openwb:www-data "$BACKUPFILE$FILENAMESUFFIX"
		sudo chmod 664 "$BACKUPFILE$FILENAMESUFFIX"
	}

	prepare_rel_db_files
	create_backup
	calculate_checksums
	cleanup_and_compress
	encrypt_backup
	fix_permissions
}

{
	generate_filename
	log_environment
	remove_old_backups
	collect_git_info
	force_mosquitto_write
	create_archive
	echo "backup finished"
} >"$LOGFILE" 2>&1

# return our filename for further processing
echo "$FILENAME$FILENAMESUFFIX"
