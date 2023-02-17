#!/bin/bash
OPENWB_BASE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
RESTORE_DIR="$OPENWB_BASE_DIR/data/restore"
SOURCE_FILE="$RESTORE_DIR/restore.tar.gz"
WORKING_DIR="/home/openwb/openwb_restore"
LOG_FILE="$OPENWB_BASE_DIR/data/log/restore.log"

declare resultMessage
declare resultStatus

{
	echo "$(date +"%Y-%m-%d %H:%M:%S") Preparation of restore started..."
	echo "****************************************"
	echo "Step 1: creating working directory \"$WORKING_DIR\""
	mkdir -p "$WORKING_DIR"
	echo "****************************************"
	echo "Step 2: extract archive to working directory"
	# extracting as root preserves file owner/group and permissions!
	if ! sudo tar --verbose --extract --file="$SOURCE_FILE" --directory="$WORKING_DIR"; then
		resultMessage="Beim Entpacken des Archivs ist ein Fehler aufgetreten!"
		resultStatus=1
	else
		echo "****************************************"
		echo "Step 3: validating extracted files"
		if [[ ! -f "$WORKING_DIR/SHA256SUM" ]] ||
			[[ ! -f "$WORKING_DIR/GIT_BRANCH" ]] ||
			[[ ! -f "$WORKING_DIR/GIT_HASH" ]] ||
			[[ ! -d "$WORKING_DIR/openWB" ]] ||
			[[ ! -f "$WORKING_DIR/mosquitto/mosquitto.db" ]] ||
			[[ ! -f "$WORKING_DIR/mosquitto_local/mosquitto.db" ]]; then
			resultMessage="Das Archiv ist nicht vollständig!"
			resultStatus=1
		else
			if ! (cd "$WORKING_DIR" && sudo sha256sum --quiet --check "SHA256SUM"); then
				resultMessage="Einige Dateien wurden gelöscht oder bearbeitet!"
				resultStatus=1
			else
				echo "****************************************"
				echo "Step 4: sync with git"
				GIT_REMOTE="origin"
				BRANCH=$(<"$WORKING_DIR/GIT_BRANCH")
				# TAG=$(<"$WORKING_DIR/GIT_HASH")
				echo "Step 5.1: fetch info from git"
				if ! git -C "$OPENWB_BASE_DIR" fetch -v "$GIT_REMOTE"; then
					resultMessage="Beim Abgleich mit dem openWB Git ist ein Fehler aufgetreten!"
					resultStatus=1
				else
					echo "Step 5.2: verify branch \"$BRANCH\" from archive"
					if ! git -C "$OPENWB_BASE_DIR" branch | grep "$BRANCH"; then
						resultMessage="Der Entwicklungszweig \"$BRANCH\" des Archivs ist ungültig."
						resultStatus=1
					else
						# set trigger for restore (checked in atreboot.sh)
						touch "${OPENWB_BASE_DIR}/data/restore/run_on_boot"
						resultMessage="Wiederherstellung vorbereitet. System wird neu gestartet."
						resultStatus=0
					fi
				fi
			fi
		fi
	fi
	if ((resultStatus != 0)); then
		echo "cleanup after error"
		sudo rm "$SOURCE_FILE"
		sudo rm -R "$WORKING_DIR"
	fi
} >"$LOG_FILE" 2>&1

echo "$resultMessage"
exit $resultStatus
