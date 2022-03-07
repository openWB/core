#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "$0")/../" && pwd)
LOGFILE="${OPENWBBASEDIR}/ramdisk/update.log"

echo "#### running update ####" > "$LOGFILE"

{
	# fetch new release from GitHub
	cd "$OPENWBBASEDIR" || exit
	echo "#### 1. fetching latest data from origin ####"
	git fetch -v origin && echo "#### done"

	# stop openwb2 service
	echo "#### 2. stopping openwb2 service ####"
	sudo service openwb2 stop && echo "#### done"

	# only master branch yet
	echo "#### 3. applying latest changes ####"
	git reset --hard "origin/master" && echo "#### done"

	# now reboot system
	echo "#### 4. rebooting system ####"
	sudo reboot now
} >> "$LOGFILE" 2>&1
