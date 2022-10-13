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
	echo "Step 1: stop openwb and mosquitto services"
	sudo systemctl stop openwb2.service mosquitto.service mosquitto_local.service
	# give systemctl some time to finish, may be unnecessary?
	sleep 2
	echo "****************************************"
	echo "Step 2: creating working directory \"$WORKINGDIR\""
	mkdir -p "$WORKINGDIR"
	echo "****************************************"
	echo "Step 3: extract archive to working directory"
	# extracting as root preserves file owner/group and permissions!
	if ! sudo tar --verbose --extract --file="$SOURCEFILE" --directory="$WORKINGDIR"; then
		echo "something went wrong! aborting restore"
		exit 1
	fi
	echo "****************************************"
	echo "Step 4: validating extracted files"
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
	echo "Step 5: sync with git"
	GITREMOTE="origin"
	BRANCH=$(<"$WORKINGDIR/GIT_BRANCH")
	TAG=$(<"$WORKINGDIR/GIT_HASH")
	echo "Step 5.1: fetch info from git"
	if ! git -C "$OPENWBBASEDIR" fetch -v "$GITREMOTE"; then
		echo "something went wrong! aborting restore"
		exit 1
	fi
	echo "Step 5.2: verify branch \"$BRANCH\" from archive"
	if ! git -C "$OPENWBBASEDIR" branch | grep "$BRANCH"; then
		echo "branch \"$BRANCH\" from backup file was not found in git! aborting restore"
		exit 1
	fi
	echo "Step 5.3: checkout branch: $BRANCH"
	if ! git -C "$OPENWBBASEDIR" checkout --force "$BRANCH"; then
		echo "checkout of branch \"$BRANCH\" failed! aborting restore"
		exit 1
	fi
	echo "Step 5.4: reset to matching version: [$TAG]"
	if ! git -C "$OPENWBBASEDIR" reset --hard "$TAG"; then
		echo "reset to version [$TAG] failed! aborting restore"
		exit 1
	fi
	echo "****************************************"
	echo "Step 6: restore contents of backup"
	# we use cp not mv because of not empty directories in destination
	# dotglob is needed to include files and directories beginning with a dot
	(shopt -s dotglob; sudo cp -v -p -r "${WORKINGDIR}${OPENWBBASEDIR}/"* "${OPENWBBASEDIR}/")
	echo "****************************************"
	echo "Step 7: restore mosquitto db"
	if [[ -f "${WORKINGDIR}${MOSQUITTODIR}/mosquitto.db" ]]; then
		sudo mv -v -f "${WORKINGDIR}${MOSQUITTODIR}/mosquitto.db" "$MOSQUITTODIR/mosquitto.db"
	else
		echo "Backup does not contain mosquitto.db. Skipping restore."
	fi
	if [[ -f "${WORKINGDIR}${MOSQUITTOLOCALDIR}/mosquitto.db" ]]; then
		sudo mv -v -f "${WORKINGDIR}${MOSQUITTOLOCALDIR}/mosquitto.db" "$MOSQUITTOLOCALDIR/mosquitto.db"
	else
		echo "Backup does not contain local mosquitto.db. Skipping restore."
	fi
	echo "****************************************"
	echo "Step 8: cleanup after restore"
	sudo rm "$SOURCEFILE"
	sudo rm -R "$WORKINGDIR"
	echo "****************************************"
	echo "$(date +"%Y-%m-%d %H:%M:%S") restore finished"
	echo "rebooting system"
	sudo reboot
} >"$LOGFILE" 2>&1
