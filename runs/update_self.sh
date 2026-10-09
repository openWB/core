#!/bin/bash
OPENWB_BASE_DIR=$(cd "$(dirname "$0")/../" && pwd)
LOG_FILE="${OPENWB_BASE_DIR}/data/log/update.log"
GIT_REMOTE="origin"
SELECTED_BRANCH="$1"
DEFAULT_TAG="*HEAD*"
SELECTED_TAG="${2:-$DEFAULT_TAG}"
DRY_RUN=1 # set to 1 for testing without writing to files or publishing to MQTT

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

checkoutTag() {
	local tag=$1
	if [[ -n $tag ]]; then
		validateTag "$tag" || return 1
		echo "#### checking out tag '$tag' ####"
		if [[ $DRY_RUN -eq 0 ]]; then
			git -C "$OPENWB_BASE_DIR" checkout --detach --force "refs/tags/$tag" || return 1
			git -C "$OPENWB_BASE_DIR" config --local openwb.updateBranch "$SELECTED_BRANCH" || return 1
			echo "#### done"
		else
			echo "DRY RUN: would checkout tag '$tag'"
		fi
	fi
}

validateBranch() {
	local branch=$1
	if ! git -C "$OPENWB_BASE_DIR" show-ref --verify --quiet "refs/remotes/$GIT_REMOTE/$branch"; then
		echo "#### ERROR: remote branch '$GIT_REMOTE/$branch' does not exist ####"
		return 1
	fi
	return 0
}

checkoutBranch() {
	local branch=$1
	if [[ -n $branch ]]; then
		echo "#### checking out branch '$branch' ####"
		if [[ $DRY_RUN -eq 0 ]]; then
			git -C "$OPENWB_BASE_DIR" checkout --force -B "$branch" --track "refs/remotes/$GIT_REMOTE/$branch" || return 1
			git -C "$OPENWB_BASE_DIR" config --local --unset-all openwb.updateBranch
			local configStatus=$?
			if [[ $configStatus -ne 0 && $configStatus -ne 5 ]]; then
				return "$configStatus"
			fi
			echo "#### done"
		else
			echo "DRY RUN: would checkout branch '$branch' from '$GIT_REMOTE/$branch'"
		fi
	fi
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
	git -C "$OPENWB_BASE_DIR" fetch -v --prune --tags --prune-tags --force "$GIT_REMOTE" || exit 1
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

	# checkout tag if selected and branch is "Release" or "Beta", as tags are not part of any branch
	if [[ $SELECTED_BRANCH == "Release" || $SELECTED_BRANCH == "Beta" ]]; then
		if [[ -n $SELECTED_TAG ]] && [[ $SELECTED_TAG != "$DEFAULT_TAG" ]]; then
			echo "#### 2. checkout selected tag '$SELECTED_TAG' for virtual branch '$SELECTED_BRANCH' ####"
			checkoutTag "$SELECTED_TAG" || exit 1
		else
			echo "#### ERROR: no tag available for virtual branch '$SELECTED_BRANCH', aborting update ####"
			exit 1
		fi
	else
		# checkout selected branch
		echo "#### 2. checkout selected branch ####"
		if ! validateBranch "$SELECTED_BRANCH"; then
			echo "#### ERROR: selected remote branch '$GIT_REMOTE/$SELECTED_BRANCH' does not exist, aborting update ####"
			exit 1
		fi
		checkoutBranch "$SELECTED_BRANCH" || exit 1
		# set Selected_Tag to default if branch is not "master"
		if [[ $SELECTED_BRANCH != "master" ]]; then
			echo "#### branch '$SELECTED_BRANCH' is not 'master', ignoring selected tag and using default tag '$DEFAULT_TAG' ####"
			SELECTED_TAG="$DEFAULT_TAG"
		fi
		# reset to latest revision or selected tag
		echo "#### 3. reset working dir ###"
		resetTarget="refs/remotes/$GIT_REMOTE/$SELECTED_BRANCH"
		echo "#### SELECTED_TAG: $SELECTED_TAG ####"
		if [[ -n $SELECTED_TAG ]] && [[ $SELECTED_TAG != "$DEFAULT_TAG" ]]; then
			echo "#### resetting working dir to selected tag '$SELECTED_TAG' ####"
			resetTarget="refs/tags/$SELECTED_TAG"
		else
			echo "#### no tag or default selected, resetting to latest remote revision"
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
