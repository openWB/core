#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
RESTOREDIR="$OPENWBBASEDIR/data/restore"
SOURCEFILE="$RESTOREDIR/restore.tar.gz"
WORKINGDIR="/home/openwb/openwb_restore"
MOSQUITTODIR="/var/lib/mosquitto"
MOSQUITTOLOCALDIR="/var/lib/mosquitto_local"
LOGFILE="$OPENWBBASEDIR/data/log/restore.log"

{
	echo "$(date +"%Y-%m-%d %H:%M:%S") Restore of backup started..."
	echo "****************************************"
	echo "Step 1: validating extracted files"
	if [[ ! -f "$WORKINGDIR/SHA256SUM" ]] || \
		[[ ! -f "$WORKINGDIR/GIT_BRANCH" ]] || \
		[[ ! -f "$WORKINGDIR/GIT_HASH" ]] || \
		[[ ! -d "$WORKINGDIR/openWB" ]] || \
		[[ ! -f "$WORKINGDIR/mosquitto/mosquitto.db" ]] || \
		[[ ! -f "$WORKINGDIR/mosquitto_local/mosquitto.db" ]]
	then
		echo "this is not a complete archive! aborting restore"
		exit 1
	fi
	if ! (cd "$WORKINGDIR" && sudo sha256sum --quiet --check "SHA256SUM"); then
		echo "some files were modified or removed! aborting restore"
		exit 1
	fi
	echo "****************************************"
	echo "Step 2: stop openwb and mosquitto services"
	sudo systemctl stop openwb2.service mosquitto.service mosquitto_local.service
	# give systemctl some time to finish, may be unnecessary?
	sleep 2
	echo "****************************************"
	echo "Step 3: sync with git"
	# GITREMOTE="origin"
	BRANCH=$(<"$WORKINGDIR/GIT_BRANCH")
	TAG=$(<"$WORKINGDIR/GIT_HASH")
	echo "Step 3.1: checkout branch: $BRANCH"
	if ! git -C "$OPENWBBASEDIR" checkout --force "$BRANCH"; then
		echo "checkout of branch \"$BRANCH\" failed! aborting restore"
		exit 1
	fi
	echo "Step 3.2: reset to matching version: [$TAG]"
	if ! git -C "$OPENWBBASEDIR" reset --hard "$TAG"; then
		echo "reset to version [$TAG] failed! aborting restore"
		exit 1
	fi
	echo "****************************************"
	echo "Step 4: restore contents of backup"
	# we use cp not mv because of not empty directories in destination
	sudo cp -v -p -r "${WORKINGDIR}/openWB/." "${OPENWBBASEDIR}/"
	echo "****************************************"
	echo "Step 5: restore mosquitto db"
	if [[ -f "${WORKINGDIR}/mosquitto/mosquitto.db" ]]; then
		sudo mv -v -f "${WORKINGDIR}/mosquitto/mosquitto.db" "$MOSQUITTODIR/mosquitto.db"
	else
		echo "Backup does not contain mosquitto.db. Skipping restore."
	fi
	if [[ -f "${WORKINGDIR}/mosquitto_local/mosquitto.db" ]]; then
		sudo mv -v -f "${WORKINGDIR}/mosquitto_local/mosquitto.db" "$MOSQUITTOLOCALDIR/mosquitto.db"
	else
		echo "Backup does not contain local mosquitto.db. Skipping restore."
	fi
	echo "****************************************"
	echo "Step 6: cleanup after restore"
	sudo rm "$SOURCEFILE"
	sudo rm -R "$WORKINGDIR"
	echo "****************************************"
	echo "$(date +"%Y-%m-%d %H:%M:%S") restore finished"
	echo "rebooting system"
	sudo reboot
} >>"$LOGFILE" 2>&1
