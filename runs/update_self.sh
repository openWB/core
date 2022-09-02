#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "$0")/../" && pwd)
LOGFILE="${OPENWBBASEDIR}/data/log/update.log"
GITREMOTE="origin"
# ToDo: get user selected branch
SELECTEDBRANCH="master"

echo "#### running update ####" > "$LOGFILE"

{
	# fetch new release from GitHub
	echo "#### 1. fetching latest data from $GITREMOTE ####"
	git -C "$OPENWBBASEDIR" fetch -v "$GITREMOTE" && echo "#### done"

	# without tags yet
	echo "#### 2. applying latest changes ####"
	git -C "$OPENWBBASEDIR" reset --hard "$GITREMOTE/$SELECTEDBRANCH" && echo "#### done"

	# now reboot system
	echo "#### 3. rebooting system ####"
	sudo reboot now &
} >> "$LOGFILE" 2>&1
