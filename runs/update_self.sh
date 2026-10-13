#!/bin/bash
OPENWB_BASE_DIR=$(cd "$(dirname "$0")/../" && pwd)
LOG_FILE="${OPENWB_BASE_DIR}/data/log/update.log"
GIT_REMOTE="origin"
SELECTED_BRANCH="$1"
DEFAULT_TAG="*HEAD*"
SELECTED_TAG="${2:-$DEFAULT_TAG}"
DRY_RUN=0 # set to 1 for testing without writing to files or publishing to MQTT

source "$OPENWB_BASE_DIR/runs/update_version_helpers.sh"

validateTag() {
	local tag=$1
	if ! git -C "$OPENWB_BASE_DIR" show-ref --verify --quiet "refs/tags/$tag"; then
		echo "#### ERROR: tag '$tag' does not exist ####"
		return 1
	fi
	if ! git -C "$OPENWB_BASE_DIR" rev-parse --verify --quiet "refs/tags/$tag^{commit}" >/dev/null; then
		echo "#### ERROR: tag '$tag' does not resolve to a commit ####"
		return 1
	fi
	if [[ $SELECTED_BRANCH == "Release" || $SELECTED_BRANCH == "Beta" ]]; then
		if ! tagMatchesTrain "$SELECTED_BRANCH" "$tag"; then
			echo "#### ERROR: tag '$tag' does not belong to train '$SELECTED_BRANCH' ####"
			return 1
		fi
	fi
	return 0
}

validateBranch() {
	local branch=$1
	if ! remoteBranchExists "$OPENWB_BASE_DIR" "$GIT_REMOTE" "$branch"; then
		echo "#### ERROR: remote branch '$GIT_REMOTE/$branch' does not exist ####"
		return 1
	fi
	return 0
}

clearUpdateFlagOnFailure() {
	local status=$?
	if [[ $status -ne 0 && $DRY_RUN -eq 0 ]]; then
		mosquitto_pub -p 1886 -t "openWB/system/update_in_progress" -r -m 'false' || true
	fi
}
trap clearUpdateFlagOnFailure EXIT

echo "#### running update ####" >"$LOG_FILE"

{
	if [[ -z $SELECTED_BRANCH ]]; then
		echo "#### ERROR: no branch selected, aborting update ####"
		exit 1
	fi

	# fetch new release from GitHub
	echo "#### 1. fetching latest data from '$GIT_REMOTE' ####"
	fetchVersionRefs "$OPENWB_BASE_DIR" "$GIT_REMOTE" || exit 1
	echo "#### done"

	if [[ -z $SELECTED_TAG ]] || [[ $SELECTED_TAG == "$DEFAULT_TAG" ]]; then
		fallbackTag=$(selectLatestTrainTag "$SELECTED_BRANCH")
		if [[ -n $fallbackTag ]]; then
			echo "#### using fallback tag '$fallbackTag' for branch '$SELECTED_BRANCH' ####"
			SELECTED_TAG="$fallbackTag"
		fi
	fi

	# check if selected tag exists
	if [[ -n $SELECTED_TAG ]] && [[ $SELECTED_TAG != "$DEFAULT_TAG" ]]; then
		if ! validateTag "$SELECTED_TAG"; then
			echo "#### ERROR: selected tag '$SELECTED_TAG' is invalid, aborting update ####"
			exit 1
		fi
	fi

	versionBranch=""
	versionRef=""
	logicalTrain=""
	if [[ $SELECTED_BRANCH == "Release" || $SELECTED_BRANCH == "Beta" ]]; then
		if [[ -n $SELECTED_TAG ]] && [[ $SELECTED_TAG != "$DEFAULT_TAG" ]]; then
			echo "#### 2. checkout selected tag '$SELECTED_TAG' for virtual branch '$SELECTED_BRANCH' ####"
			versionRef="refs/tags/$SELECTED_TAG"
			logicalTrain="$SELECTED_BRANCH"
		else
			echo "#### ERROR: no tag available for virtual branch '$SELECTED_BRANCH', aborting update ####"
			exit 1
		fi
	else
		echo "#### 2. checkout selected branch ####"
		if ! validateBranch "$SELECTED_BRANCH"; then
			echo "#### ERROR: selected remote branch '$GIT_REMOTE/$SELECTED_BRANCH' does not exist, aborting update ####"
			exit 1
		fi
		versionBranch="$SELECTED_BRANCH"
		# set Selected_Tag to default if branch is not "master"
		if [[ $SELECTED_BRANCH != "master" ]]; then
			echo "#### branch '$SELECTED_BRANCH' is not 'master', ignoring selected tag and using default tag '$DEFAULT_TAG' ####"
			SELECTED_TAG="$DEFAULT_TAG"
		fi
		versionRef="refs/remotes/$GIT_REMOTE/$SELECTED_BRANCH"
		echo "#### SELECTED_TAG: $SELECTED_TAG ####"
		if [[ -n $SELECTED_TAG ]] && [[ $SELECTED_TAG != "$DEFAULT_TAG" ]]; then
			echo "#### resetting working dir to selected tag '$SELECTED_TAG' ####"
			versionRef="refs/tags/$SELECTED_TAG"
		else
			echo "#### no tag or default selected, resetting to latest remote revision"
		fi
	fi

	echo "#### 3. apply selected version '$versionRef' ####"
	if ! applyVersion "$OPENWB_BASE_DIR" "$GIT_REMOTE" "$versionBranch" "$versionRef" "$logicalTrain" "$DRY_RUN"; then
		echo "#### ERROR: applying version '$versionRef' failed, aborting update ####"
		exit 1
	fi
	if [[ $DRY_RUN -eq 0 ]]; then
		echo "#### done"
	else
		echo "DRY RUN: would apply version '$versionRef' with branch '$versionBranch' and train '$logicalTrain'"
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
