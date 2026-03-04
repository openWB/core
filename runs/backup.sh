#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
OPENWBDIRNAME=${OPENWBBASEDIR##*/}
OPENWBDIRNAME=${OPENWBDIRNAME:-/}
TARBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
BACKUPDIR="$OPENWBBASEDIR/data/backup"
RAMDISKDIR="$OPENWBBASEDIR/ramdisk"
TEMPDIR=$(mktemp -d --tmpdir openwb_backup_XXXXXX)
LOGDIR="$OPENWBBASEDIR/data/log"
LOGFILE="$LOGDIR/backup.log"
HOMEDIR="/home/openwb"
KEYFILE="backup.key"
VAR_LIB="/var/lib"

# Mosquitto DB files to monitor
DB_FILES=(
	"mosquitto/mosquitto.db"
	"mosquitto_local/mosquitto.db"
)

# Timeout for mosquitto DB flush
DB_TIMEOUT=5

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
			if [ -e "$VAR_LIB/$f" ]; then
				BASELINE_DB_MTIME["$f"]=$(stat -c %Y "$VAR_LIB/$f")
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
		# uses inotifywait if available, else falls back to polling
		# requires inotify-tools package for inotifywait
		local start_ts
		start_ts=$(date +%s)
		declare -A initial_mtime

		# Use previously captured baseline (recorded before signal)
		if ((${#BASELINE_DB_MTIME[@]})); then
			for f in "${DB_FILES[@]}"; do
				initial_mtime["$VAR_LIB/$f"]=${BASELINE_DB_MTIME["$f"]:-0}
			done
		else
			# Fallback (should not occur)
			for f in "${DB_FILES[@]}"; do
				[ -e "$VAR_LIB/$f" ] && initial_mtime["$VAR_LIB/$f"]=$(stat -c %Y "$VAR_LIB/$f") || initial_mtime["$VAR_LIB/$f"]=0
			done
		fi

		echo "waiting for mosquitto to flush db files (timeout ${DB_TIMEOUT}s)..."

		if command -v inotifywait >/dev/null 2>&1; then
			echo "using 'inotifywait'"
			local pending=()
			for f in "${DB_FILES[@]}"; do
				pending+=("$VAR_LIB/$f")
			done
			while ((${#pending[@]})); do
				local elapsed=$(( $(date +%s) - start_ts ))
				local remain=$(( DB_TIMEOUT - elapsed ))
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
					if [ -e "$VAR_LIB/$f" ]; then
						local mt
						mt=$(stat -c %Y "$VAR_LIB/$f")
						if (( mt != initial_mtime["$VAR_LIB/$f"] )); then
							echo "modified (polling): $f (old: ${initial_mtime["$VAR_LIB/$f"]} -> new: $mt)"
							initial_mtime["$VAR_LIB/$f"]=$mt
						else
							all_ok=0
						fi
					else
						all_ok=0
					fi
				done
				local elapsed=$(( $(date +%s) - start_ts ))
				(( all_ok == 1 )) && echo "all relevant files are modified after ${elapsed}s" && break
				(( elapsed >= DB_TIMEOUT )) && echo "timeout reached (polling), continuing." && break
				sleep 0.1
			done
		fi
	}

	copy_db_to_temp() {
		echo "copying mosquitto db files to temporary location"
		for f in "${DB_FILES[@]}"; do
			if [ -e "$VAR_LIB/$f" ]; then
				local dest_dir
				dest_dir="$TEMPDIR/$(dirname "$f")"
				mkdir -p "$dest_dir"
				sudo cp -v "$VAR_LIB/$f" "$dest_dir/"
			else
				echo "skipping $f (does not exist)"
			fi
		done
	}

	collect_baseline
	flush_mosquitto
	wait_for_mosquitto_flush
	copy_db_to_temp
}

collect_git_info() {
	echo "collecting git information"
	if git branch --no-color --show-current >"$TEMPDIR/GIT_BRANCH"; then
		echo "current branch: $(<"$TEMPDIR/GIT_BRANCH")"
	else
		echo "failed to collect git branch info"
		return 1
	fi
	if git log --pretty='format:%H' -n1 >"$TEMPDIR/GIT_HASH"; then
		echo "current commit hash: $(<"$TEMPDIR/GIT_HASH")"
	else
		echo "failed to collect git commit hash"
		return 1
	fi
	return 0
}

create_archive() {
	create_backup() {
		echo "creating new backup file: $BACKUPFILE"
		echo "adding files"

		# JSON-Dateien im clients-Ordner sammeln
		json_files=()
		while IFS= read -r -d '' file; do
			json_files+=("${file#$TARBASEDIR/}")
		done < <(find "$TARBASEDIR/$OPENWBDIRNAME/data/clients" -maxdepth 1 -type f -name '*.json' -print0)

		sudo tar --verbose --create \
			--file="$BACKUPFILE" \
			--exclude=".gitignore" \
			--directory="$TEMPDIR/" \
				"${DB_FILES[@]}" \
				"GIT_BRANCH" \
				"GIT_HASH" \
			--directory="/etc/mosquitto/" \
				"conf_local.d/" \
			--directory="$TARBASEDIR/" \
				"$OPENWBDIRNAME/data/charge_log" \
				"$OPENWBDIRNAME/data/daily_log" \
				"$OPENWBDIRNAME/data/monthly_log" \
				"$OPENWBDIRNAME/data/log/uuid" \
				"${json_files[@]}" \
			--directory="$HOMEDIR/" \
				"configuration.json" \
			--directory="/" \
				"boot/config.txt"
		
		if [ -f "$VAR_LIB/mosquitto/dynamic-security.json" ]; then
			echo "adding mosquitto/dynamic-security.json"
			sudo tar --verbose --append \
				--file="$BACKUPFILE" \
				--directory="$VAR_LIB/" \
					"mosquitto/dynamic-security.json"
		else
			echo "mosquitto/dynamic-security.json not found, skipping"
		fi
		if [ -f "$HOMEDIR/.config/mosquitto_ctrl" ]; then
			echo "adding mosquitto_ctrl file"
			sudo tar --verbose --append \
				--file="$BACKUPFILE" \
				--directory="$HOMEDIR/.config/" \
					"mosquitto_ctrl"
		else
			echo "mosquitto_ctrl file not found, skipping"
		fi
	}

	calculate_checksums() {
		echo "calculating checksums"
		IFS=$'\n'
		mapfile -t file_list < <(tar -tf "$BACKUPFILE")
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
			sha256sum "$TEMPDIR/$file" | sed -n "s|$TEMPDIR/||p" >> "$TEMPDIR/SHA256SUM"
			# remove the file
			rm -f "$TEMPDIR/$file"
		done

		echo "adding checksum file to archive"
		sudo tar --verbose --append \
			--file="$BACKUPFILE" \
			--directory="$TEMPDIR/" \
				"SHA256SUM"
	}

	cleanup_and_compress() {
		echo "removing temporary files"
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
	if collect_git_info; then
		echo "git information collected successfully"
	else
		echo "error: failed to collect git information"
		exit 1
	fi
	force_mosquitto_write
	create_archive
	echo "backup finished"
} >"$LOGFILE" 2>&1

# return our filename for further processing
echo "$FILENAME$FILENAMESUFFIX"
