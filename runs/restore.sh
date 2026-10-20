#!/bin/bash
OPENWB_BASE_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
RESTORE_DIR="$OPENWB_BASE_DIR/data/restore"
SOURCE_FILE="$RESTORE_DIR/restore.tar.gz"
WORKING_DIR="/home/openwb/openwb_restore"
MOSQUITTO_DB_DIR="/var/lib/mosquitto"
MOSQUITTO_LOCAL_DB_DIR="/var/lib/mosquitto_local"
MOSQUITTO_CONF_DIR="/etc/mosquitto"
LOG_FILE="$OPENWB_BASE_DIR/data/log/restore.log"
GIT_REMOTE="origin"

source "$OPENWB_BASE_DIR/runs/update_version_helpers.sh" || exit 1

{
	echo "$(date +"%Y-%m-%d %H:%M:%S") Restore of backup started..."
	echo "****************************************"
	# already done in prepare_restore.sh:
	# Step 1: creating working directory
	# Step 2: extract archive to working directory
	# Step 3: validating extracted files
	# Step 4: sync with git
	echo "Step 5: stop mosquitto services"
	# no need to stop openwb2.service as we are in pre start script
	sudo systemctl stop mosquitto.service mosquitto_local.service
	# give systemctl some time to finish, may be unnecessary?
	sleep 2
	echo "****************************************"
	echo "Step 6: checkout matching git branch and hash"
	BRANCH=$(<"$WORKING_DIR/GIT_BRANCH")
	HASH=$(<"$WORKING_DIR/GIT_HASH")
	UPDATE_BRANCH=""
	if [[ -f "$WORKING_DIR/GIT_UPDATE_BRANCH" ]]; then
		UPDATE_BRANCH=$(<"$WORKING_DIR/GIT_UPDATE_BRANCH")
	fi
	metadataStatus=0
	validateRestoreGitMetadata "$BRANCH" "$UPDATE_BRANCH" || metadataStatus=$?
	if [[ $metadataStatus -eq 1 ]]; then
		echo "invalid logical update branch '$UPDATE_BRANCH'! aborting restore"
		exit 1
	elif [[ $metadataStatus -eq 2 ]]; then
		echo "logical update branch requires detached HEAD! aborting restore"
		exit 1
	fi
	if [[ -z $BRANCH ]]; then
		echo "checkout detached commit: $HASH"
	else
		echo "checkout branch from remote: $GIT_REMOTE/$BRANCH"
	fi
	echo "apply saved version: [$HASH]"
	if ! applyVersion "$OPENWB_BASE_DIR" "$GIT_REMOTE" "$BRANCH" "$HASH" "$UPDATE_BRANCH"; then
		echo "applying version [$HASH] failed! aborting restore"
		exit 1
	fi
	echo "****************************************"
	echo "Step 7: restore contents of backup"
	# we use cp not mv because of not empty directories in destination
	if ! sudo cp -v -p -r "${WORKING_DIR}/openWB/." "${OPENWB_BASE_DIR}/"; then
		echo "restoring openWB files failed! aborting restore"
		exit 1
	fi
	if [[ -f "$WORKING_DIR/configuration.json" ]]; then
		sudo mv -v -f "${WORKING_DIR}/configuration.json" "/home/openwb/"
	else
		echo "Backup does not contain configuration. Skipping restore."
	fi
	if [[ -f "$WORKING_DIR/mosquitto_ctrl" ]]; then
		sudo mv -v -f "${WORKING_DIR}/mosquitto_ctrl" "/home/openwb/.config/"
	else
		echo "Backup does not contain mosquitto_ctrl. Skipping restore."
	fi
	echo "****************************************"
	echo "Step 7.1: restore mosquitto db"
	if [[ -f "${WORKING_DIR}/mosquitto/mosquitto.db" ]]; then
		sudo mv -v -f "${WORKING_DIR}/mosquitto/mosquitto.db" "$MOSQUITTO_DB_DIR/mosquitto.db"
		sudo chown mosquitto:mosquitto "$MOSQUITTO_DB_DIR/mosquitto.db"
	else
		echo "Backup does not contain mosquitto.db. Skipping restore."
	fi
	if [[ -f "$WORKING_DIR/mosquitto/dynamic-security.json" ]]; then
		sudo mv -v -f "${WORKING_DIR}/mosquitto/dynamic-security.json" "/var/lib/mosquitto/"
		sudo chown mosquitto:mosquitto "/var/lib/mosquitto/dynamic-security.json"
		sudo chmod 600 "/var/lib/mosquitto/dynamic-security.json"
	else
		echo "Backup does not contain dynamic-security.json. Skipping restore."
	fi
	if [[ -f "${WORKING_DIR}/mosquitto_local/mosquitto.db" ]]; then
		sudo mv -v -f "${WORKING_DIR}/mosquitto_local/mosquitto.db" "$MOSQUITTO_LOCAL_DB_DIR/mosquitto.db"
		sudo chown mosquitto:mosquitto "$MOSQUITTO_LOCAL_DB_DIR/mosquitto.db"
	else
		echo "Backup does not contain local mosquitto.db. Skipping restore."
	fi
	echo "****************************************"
	echo "Step 7.2: restore mosquitto configuration"
	if [[ -d "${WORKING_DIR}/conf_local.d" ]]; then
		# remove old configuration
		sudo rm -v -r "$MOSQUITTO_CONF_DIR/conf_local.d"
		# copy configuration
		sudo cp -v -p -r "${WORKING_DIR}/conf_local.d" "$MOSQUITTO_CONF_DIR/"
	else
		echo "Backup does not contain mosquitto configuration. Skipping restore."
	fi
	echo "****************************************"
	echo "Step 8: restore boot file"
	if [[ -f "${WORKING_DIR}/boot/config.txt" ]]; then
		sudo mv -v -f "${WORKING_DIR}/boot/config.txt" "/boot/"
	else
		echo "Backup does not contain boot file. Skipping restore."
	fi
	echo "****************************************"
	echo "Step 9: cleanup after restore"
	sudo rm "$SOURCE_FILE"
	sudo rm -R "$WORKING_DIR"
	echo "****************************************"
	echo "$(date +"%Y-%m-%d %H:%M:%S") restore finished"
	echo "rebooting system"
	sudo reboot
} >>"$LOG_FILE" 2>&1
