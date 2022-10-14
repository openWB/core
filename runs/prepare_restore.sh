#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
RESTOREDIR="$OPENWBBASEDIR/data/restore"
SOURCEFILE="$RESTOREDIR/restore.tar.gz"
WORKINGDIR="/home/openwb/openwb_restore"
# MOSQUITTODIR="/var/lib/mosquitto"
# MOSQUITTOLOCALDIR="/var/lib/mosquitto_local"
LOGFILE="$OPENWBBASEDIR/data/log/restore.log"

declare resultMessage
declare resultStatus

{
	echo "$(date +"%Y-%m-%d %H:%M:%S") Preparation of restore started..."
	echo "****************************************"
	echo "Step 1: creating working directory \"$WORKINGDIR\""
	mkdir -p "$WORKINGDIR"
	echo "****************************************"
	echo "Step 2: extract archive to working directory"
	# extracting as root preserves file owner/group and permissions!
	if ! sudo tar --verbose --extract --file="$SOURCEFILE" --directory="$WORKINGDIR"; then
		resultMessage="Beim Entpacken des Archivs ist ein Fehler aufgetreten!"
		resultStatus=1
	else
		echo "****************************************"
		echo "Step 3: validating extracted files"
		if [[ ! -f "$WORKINGDIR/SHA256SUM" ]] || \
			[[ ! -f "$WORKINGDIR/GIT_BRANCH" ]] || \
			[[ ! -f "$WORKINGDIR/GIT_HASH" ]] || \
			[[ ! -d "$WORKINGDIR/openWB" ]] || \
			[[ ! -f "$WORKINGDIR/mosquitto/mosquitto.db" ]] || \
			[[ ! -f "$WORKINGDIR/mosquitto_local/mosquitto.db" ]]
		then
			resultMessage="Das Archiv ist nicht vollständig!"
			resultStatus=1
		else
			if ! (cd "$WORKINGDIR" && sudo sha256sum --quiet --check "SHA256SUM"); then
				resultMessage="Einige Dateien wurden gelöscht oder bearbeitet!"
				resultStatus=1
			else
				echo "****************************************"
				echo "Step 4: sync with git"
				GITREMOTE="origin"
				BRANCH=$(<"$WORKINGDIR/GIT_BRANCH")
				# TAG=$(<"$WORKINGDIR/GIT_HASH")
				echo "Step 5.1: fetch info from git"
				if ! git -C "$OPENWBBASEDIR" fetch -v "$GITREMOTE"; then
					resultMessage="Beim Abgleich mit dem openWB Git ist ein Fehler aufgetreten!"
					resultStatus=1
				else
					echo "Step 5.2: verify branch \"$BRANCH\" from archive"
					if ! git -C "$OPENWBBASEDIR" branch | grep "$BRANCH"; then
						resultMessage="Der Entwicklungszweig \"$BRANCH\" des Archivs ist ungültig."
						resultStatus=1
					else
						# set trigger for restore (checked in atreboot.sh)
						touch "${OPENWBBASEDIR}/data/restore/run_on_boot"
						resultMessage="Wiederherstellung vorbereitet. System wird neu gestartet."
						resultStatus=0
					fi
				fi
			fi
		fi
	fi
	if ((resultStatus != 0)); then
		echo "cleanup after error"
		sudo rm "$SOURCEFILE"
		sudo rm -R "$WORKINGDIR"
	fi
} >"$LOGFILE" 2>&1

echo "$resultMessage"
exit $resultStatus
