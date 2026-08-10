#!/bin/bash
OPENWB_BASE_DIR=$(cd "$(dirname "$0")/../" && pwd)
LOG_FILE="${OPENWB_BASE_DIR}/data/log/update.log"
GIT_REMOTE="origin"
SELECTED_BRANCH="$1"
DEFAULT_TAG="*HEAD*"
SELECTED_TAG="${2:-$DEFAULT_TAG}"
DRY_RUN=1 # set to 1 for testing without writing to files or publishing to MQTT

latestTagByPattern() {
	local pattern=$1
	git -C "$OPENWB_BASE_DIR" tag --sort=-version:refname | grep -E -m1 "$pattern"
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

	case "$SELECTED_BRANCH" in
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

validateTag() {
	local tag=$1
	if ! git -C "$OPENWB_BASE_DIR" rev-parse --verify --quiet "$tag" >/dev/null; then
		echo "#### ERROR: tag '$tag' does not exist ####"
		return 1
	fi
	return 0
}

checkoutTag() {
	local tag=$1
	if [[ -n $tag ]]; then
		validateTag "$tag" || return 1
		echo "#### checking out tag '$tag' ####"
		if [[ $DRY_RUN -eq 0 ]]; then
			git -C "$OPENWB_BASE_DIR" checkout --force "$tag" && echo "#### done"
		else
			echo "DRY RUN: would checkout tag '$tag'"
		fi
	fi
}

validateBranch() {
	local branch=$1
	if ! git -C "$OPENWB_BASE_DIR" show-ref --verify --quiet "refs/heads/$branch"; then
		echo "#### ERROR: local branch '$branch' does not exist ####"
		return 1
	fi
	return 0
}

checkoutBranch() {
	local branch=$1
	if [[ -n $branch ]]; then
		echo "#### checking out branch '$branch' ####"
		if [[ $DRY_RUN -eq 0 ]]; then
			git -C "$OPENWB_BASE_DIR" checkout --force "$branch" && echo "#### done"
		else
			echo "DRY RUN: would checkout branch '$branch'"
		fi
	fi
}

echo "#### running update ####" >"$LOG_FILE"

{
	if [[ -z $SELECTED_BRANCH ]]; then
		echo "#### ERROR: no branch selected, aborting update ####"
		exit 1
	fi

	# fetch new release from GitHub
	echo "#### 1. fetching latest data from '$GIT_REMOTE' ####"
	git -C "$OPENWB_BASE_DIR" fetch -v "$GIT_REMOTE" && echo "#### done"

	if [[ -z $SELECTED_TAG ]] || [[ $SELECTED_TAG == "$DEFAULT_TAG" ]]; then
		fallbackTag=$(selectFallbackTag)
		if [[ -n $fallbackTag ]]; then
			echo "#### using fallback tag '$fallbackTag' for branch '$SELECTED_BRANCH' ####"
			SELECTED_TAG="$fallbackTag"
		fi
	fi

	# check if selected tag exists
	if [[ -n $SELECTED_TAG ]] && [[ $SELECTED_TAG != "$DEFAULT_TAG" ]]; then
		if ! validateTag "$SELECTED_TAG"; then
			echo "#### ERROR: selected tag '$SELECTED_TAG' does not exist, aborting update ####"
			exit 1
		fi
	fi

	# checkout tag if selected and branch is "Release" or "Beta", as tags are not part of any branch
	if [[ $SELECTED_BRANCH == "Release" || $SELECTED_BRANCH == "Beta" ]]; then
		if [[ -n $SELECTED_TAG ]] && [[ $SELECTED_TAG != "$DEFAULT_TAG" ]]; then
			echo "#### 2. checkout selected tag '$SELECTED_TAG' for virtual branch '$SELECTED_BRANCH' ####"
			checkoutTag "$SELECTED_TAG"
		fi
	else
		# checkout selected branch
		echo "#### 2. checkout selected branch ####"
		if ! validateBranch "$SELECTED_BRANCH"; then
			echo "#### ERROR: selected branch '$SELECTED_BRANCH' does not exist, aborting update ####"
			exit 1
		fi
		checkoutBranch "$SELECTED_BRANCH"
		# set Selected_Tag to default if branch is not "master"
		if [[ $SELECTED_BRANCH != "master" ]]; then
			echo "#### branch '$SELECTED_BRANCH' is not 'master', ignoring selected tag and using default tag '$DEFAULT_TAG' ####"
			SELECTED_TAG="$DEFAULT_TAG"
		fi
		# reset to latest revision or selected tag
		echo "#### 3. reset working dir ###"
		resetTarget="$GIT_REMOTE/$SELECTED_BRANCH"
		echo "#### SELECTED_TAG: $SELECTED_TAG ####"
		if [[ -n $SELECTED_TAG ]] && [[ $SELECTED_TAG != "$DEFAULT_TAG" ]]; then
			echo "#### resetting working dir to selected tag '$SELECTED_TAG' ####"
			resetTarget="$SELECTED_TAG"
		else
			if git -C "$OPENWB_BASE_DIR" show-ref --verify --quiet "refs/remotes/$GIT_REMOTE/$SELECTED_BRANCH"; then
				echo "#### no tag or default selected, resetting to latest revision"
			else
				echo "#### no remote branch '$GIT_REMOTE/$SELECTED_BRANCH', keeping current checkout ####"
				resetTarget="HEAD"
			fi
		fi

		if [[ $DRY_RUN -eq 0 ]]; then
			echo "#### resetting working dir to '$resetTarget' ####"
			git -C "$OPENWB_BASE_DIR" reset --hard "$resetTarget" && echo "#### done"
		else
			echo "DRY RUN: would reset working dir to '$resetTarget'"
		fi
	fi

	# clean mosquitto configuration directory to remove possibly outdated files
	echo "#### 4. clean mosquitto configuration, will be recreated on next boot ####"
	if [[ $DRY_RUN -eq 0 ]]; then
		sudo rm -v -f /etc/mosquitto/conf.d/openwb-*.conf
	else
		echo "DRY RUN: would remove /etc/mosquitto/conf.d/openwb-*.conf"
	fi

	# notify system
	# set boot_done first to prevent flickering in gui
	if [[ $DRY_RUN -eq 0 ]]; then
		mosquitto_pub -p 1886 -t "openWB/system/boot_done" -r -m 'false'
		mosquitto_pub -p 1886 -t "openWB/system/update_in_progress" -r -m 'false'
	else
		echo "DRY RUN: would publish to MQTT topics 'openWB/system/boot_done' and 'openWB/system/update_in_progress'"
	fi
	sleep 1

	# now reboot system
	echo "#### 5. rebooting system ####"
	if [[ $DRY_RUN -eq 0 ]]; then
		sudo reboot now &
	else
		echo "DRY RUN: would reboot system now"
	fi
} >>"$LOG_FILE" 2>&1
