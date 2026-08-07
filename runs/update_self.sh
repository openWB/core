#!/bin/bash
OPENWBBASEDIR=$(cd "$(dirname "$0")/../" && pwd)
LOGFILE="${OPENWBBASEDIR}/data/log/update.log"
GITREMOTE="origin"
SELECTEDBRANCH="$1"
DEFAULTTAG="*HEAD*"
SELECTEDTAG=$2

latestTagByPattern() {
	local pattern=$1
	git -C "$OPENWBBASEDIR" tag --sort=-version:refname | grep -E -m1 "$pattern"
}

extractBaseVersion() {
	local tag=$1
	echo "$tag" | sed -E 's/-Patch\.[0-9]+$//; s/-Beta\.[0-9]+$//; s/-[Rr][Cc]\.[0-9]+$//'
}

highestBaseByPattern() {
	local pattern=$1
	local tag
	tag=$(latestTagByPattern "$pattern") || return 1
	extractBaseVersion "$tag"
}

selectFallbackTag() {
	local baseVersion
	local basePattern

	case "$SELECTEDBRANCH" in
	"Release")
		baseVersion=$(highestBaseByPattern '^[0-9]+\.[0-9]+\.[0-9]+(-Patch\.[0-9]+)?$') || return 1
		basePattern=${baseVersion//./\\.}
		latestTagByPattern "^${basePattern}-Patch\\.[0-9]+$" ||
			latestTagByPattern "^${basePattern}$"
		;;
	"Beta")
		baseVersion=$(highestBaseByPattern '^[0-9]+\.[0-9]+\.[0-9]+(-Patch\.[0-9]+|-Beta\.[0-9]+|-[Rr][Cc]\.[0-9]+)?$') || return 1
		basePattern=${baseVersion//./\\.}
		latestTagByPattern "^${basePattern}-Patch\\.[0-9]+$" ||
			latestTagByPattern "^${basePattern}$" ||
			latestTagByPattern "^${basePattern}-[Rr][Cc]\\.[0-9]+$" ||
			latestTagByPattern "^${basePattern}-Beta\\.[0-9]+$"
		;;
	*)
		return 1
		;;
	esac
}

echo "#### running update ####" >"$LOGFILE"

{
	# fetch new release from GitHub
	echo "#### 1. fetching latest data from '$GITREMOTE' ####"
	git -C "$OPENWBBASEDIR" fetch -v "$GITREMOTE" && echo "#### done"

	if [[ -z $SELECTEDTAG ]] || [[ $SELECTEDTAG == "$DEFAULTTAG" ]]; then
		fallbackTag=$(selectFallbackTag)
		if [[ -n $fallbackTag ]]; then
			echo "#### using fallback tag '$fallbackTag' for branch '$SELECTEDBRANCH' ####"
			SELECTEDTAG="$fallbackTag"
		fi
	fi

	# checkout selected branch
	echo "#### 2. checkout selected branch '$SELECTEDBRANCH'"
	if git -C "$OPENWBBASEDIR" show-ref --verify --quiet "refs/heads/$SELECTEDBRANCH"; then
		git -C "$OPENWBBASEDIR" checkout --force "$SELECTEDBRANCH" && echo "#### done"
	else
		echo "#### ERROR: local branch '$SELECTEDBRANCH' not found, aborting update ####"
		exit 1
	fi

	# reset to latest revision or selected tag
	echo "#### 3. reset working dir ###"
	resetTarget="$GITREMOTE/$SELECTEDBRANCH"
	echo "SELECTEDTAG: $SELECTEDTAG"
	if [[ -n $SELECTEDTAG ]] && [[ $SELECTEDTAG != "$DEFAULTTAG" ]]; then
		echo "#### selected tag: '$SELECTEDTAG'"
		resetTarget="$SELECTEDTAG"
	else
		if git -C "$OPENWBBASEDIR" show-ref --verify --quiet "refs/remotes/$GITREMOTE/$SELECTEDBRANCH"; then
			echo "#### no tag or default selected, resetting to latest revision"
		else
			echo "#### no remote branch '$GITREMOTE/$SELECTEDBRANCH', keeping current checkout ####"
			resetTarget="HEAD"
		fi
	fi
	git -C "$OPENWBBASEDIR" reset --hard "$resetTarget" && echo "#### done"

	# clean mosquitto configuration directory to remove possibly outdated files
	echo "#### 4. clean mosquitto configuration, will be recreated on next boot"
	sudo rm -v -f /etc/mosquitto/conf.d/openwb-*.conf

	# notify system
	# set boot_done first to prevent flickering in gui
	mosquitto_pub -p 1886 -t "openWB/system/boot_done" -r -m 'false'
	mosquitto_pub -p 1886 -t "openWB/system/update_in_progress" -r -m 'false'
	sleep 1

	# now reboot system
	echo "#### 5. rebooting system ####"
	sudo reboot now &
} >>"$LOGFILE" 2>&1
