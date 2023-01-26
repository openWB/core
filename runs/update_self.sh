#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "$0")/../" && pwd)
LOGFILE="${OPENWBBASEDIR}/data/log/update.log"
GITREMOTE="origin"
SELECTEDBRANCH="$1"
DEFAULTTAG="*HEAD*"
# ToDo: honor selected tag
SELECTEDTAG=$2

echo "#### running update ####" >"$LOGFILE"

{
	# notify system about running update
	mosquitto_pub -p 1886 -t "openWB/system/update_in_progress" -r -m 'true'

	# fetch new release from GitHub
	echo "#### 1. fetching latest data from '$GITREMOTE' ####"
	git -C "$OPENWBBASEDIR" fetch -v "$GITREMOTE" && echo "#### done"

	# checkout selected branch
	echo "#### 2. checkout selected branch '$SELECTEDBRANCH'"
	git -C "$OPENWBBASEDIR" checkout --force "$SELECTEDBRANCH" && echo "#### done"

	# reset to latest revision or selected tag
	echo "#### 3. reset working dir ###"
	resetTarget="$GITREMOTE/$SELECTEDBRANCH"
	echo "SELECTEDTAG: $SELECTEDTAG"
	if [[ -n $SELECTEDTAG ]] && [[ $SELECTEDTAG != "$DEFAULTTAG" ]]; then
		echo "#### selected tag: '$SELECTEDTAG'"
		resetTarget="$SELECTEDTAG"
	else
		echo "#### no tag or default selected, resetting to latest revision"
	fi
	git -C "$OPENWBBASEDIR" reset --hard "$resetTarget" && echo "#### done"

	# now reboot system
	echo "#### 4. rebooting system ####"
	sudo reboot now &
} >>"$LOGFILE" 2>&1
