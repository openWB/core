#!/bin/bash
OPENWB_BASE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
RESTORE_DIR="$OPENWB_BASE_DIR/data/restore"
SOURCE_FILE="$RESTORE_DIR/restore.tar.gz"
WORKING_DIR="/home/openwb/openwb_restore"
MOSQUITTO_DIR="/var/lib/mosquitto"
MOSQUITTO_LOCAL_DIR="/var/lib/mosquitto_local"
LOG_FILE="$OPENWB_BASE_DIR/data/log/restore.log"

{
	echo "$(date +"%Y-%m-%d %H:%M:%S") Restore of backup started..."
	echo "****************************************"
	echo "Step 1: validating extracted files"
	if [[ ! -f "$WORKING_DIR/SHA256SUM" ]] ||
		[[ ! -f "$WORKING_DIR/GIT_BRANCH" ]] ||
		[[ ! -f "$WORKING_DIR/GIT_HASH" ]] ||
		[[ ! -d "$WORKING_DIR/openWB" ]] ||
		[[ ! -f "$WORKING_DIR/mosquitto/mosquitto.db" ]] ||
		[[ ! -f "$WORKING_DIR/mosquitto_local/mosquitto.db" ]]; then
		echo "this is not a complete archive! aborting restore"
		exit 1
	fi
	if ! (cd "$WORKING_DIR" && sudo sha256sum --quiet --check "SHA256SUM"); then
		echo "some files were modified or removed! aborting restore"
		exit 1
	fi
	echo "****************************************"
	echo "Step 2: stop mosquitto services"
	# no need to stop openwb2.service as we are in pre start script
	sudo systemctl stop mosquitto.service mosquitto_local.service
	# give systemctl some time to finish, may be unnecessary?
	sleep 2
	echo "****************************************"
	echo "Step 3: sync with git"
	BRANCH=$(<"$WORKING_DIR/GIT_BRANCH")
	TAG=$(<"$WORKING_DIR/GIT_HASH")
	echo "Step 3.1: checkout branch: $BRANCH"
	if ! git -C "$OPENWB_BASE_DIR" checkout --force "$BRANCH"; then
		echo "checkout of branch \"$BRANCH\" failed! aborting restore"
		exit 1
	fi
	echo "Step 3.2: reset to matching version: [$TAG]"
	if ! git -C "$OPENWB_BASE_DIR" reset --hard "$TAG"; then
		echo "reset to version [$TAG] failed! aborting restore"
		exit 1
	fi
	echo "****************************************"
	echo "Step 4: restore contents of backup"
	# we use cp not mv because of not empty directories in destination
	sudo cp -v -p -r "${WORKING_DIR}/openWB/." "${OPENWB_BASE_DIR}/"
	echo "****************************************"
	echo "Step 5: restore mosquitto db"
	if [[ -f "${WORKING_DIR}/mosquitto/mosquitto.db" ]]; then
		sudo mv -v -f "${WORKING_DIR}/mosquitto/mosquitto.db" "$MOSQUITTO_DIR/mosquitto.db"
	else
		echo "Backup does not contain mosquitto.db. Skipping restore."
	fi
	if [[ -f "${WORKING_DIR}/mosquitto_local/mosquitto.db" ]]; then
		sudo mv -v -f "${WORKING_DIR}/mosquitto_local/mosquitto.db" "$MOSQUITTO_LOCAL_DIR/mosquitto.db"
	else
		echo "Backup does not contain local mosquitto.db. Skipping restore."
	fi
	echo "****************************************"
	echo "Step 6: cleanup after restore"
	sudo rm "$SOURCE_FILE"
	sudo rm -R "$WORKING_DIR"
	echo "****************************************"
	echo "$(date +"%Y-%m-%d %H:%M:%S") restore finished"
	echo "rebooting system"
	sudo reboot
} >>"$LOG_FILE" 2>&1
