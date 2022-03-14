#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "$0")/../" && pwd)
LOGFILE="${OPENWBBASEDIR}/ramdisk/update.log"

echo "#### running update ####" > "$LOGFILE"

{
	# fetch new release from GitHub
	cd "$OPENWBBASEDIR" || exit
	echo "#### 1. fetching latest data from origin ####"
	git fetch -v origin && echo "#### done"

	# only master branch without tags yet
	echo "#### 2. applying latest changes ####"
	git reset --hard "origin/master" && echo "#### done"

	# now reboot system
	echo "#### 3. rebooting system ####"
	sudo reboot now &
} >> "$LOGFILE" 2>&1
